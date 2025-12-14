# Author - Abhishek Rajgaria
# Date - 27th Oct 2024
# Summary - Helper method for executing batch request

import os
import sys
import time
import random
import argparse
import pandas as pd
from tqdm import tqdm
import concurrent.futures
from loguru import logger
from dotenv import load_dotenv
from gemini_model import get_gemini
from pymongo.server_api import ServerApi
from pymongo import MongoClient, UpdateOne
import traceback

from openai import OpenAI

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import requests  # Add this import at the top


from gpt_utils import *

os.makedirs("logs", exist_ok=True)
logger.add("logs/app_hybridqa.log", level="DEBUG")

# Add prompt to the system path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "three_prompts"))
)


MAX_RETRY = 5
RETRY_DELAY = 5


def get_mongodb_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI_BASELINE")
    return MongoClient(uri, server_api=ServerApi("1"))


def get_prompts_from_mongodb(client, dataset, reasoning, **kwargs):
    db = client[dataset]
    collection = db["prompts"]
    # print("collection", collection)
    reasoning_values = [reasoning]
    documents = collection.find(
        {
            "reasoning": {"$in": reasoning_values}
        },  # Match reasoning field to meta_s1, meta_s2, meta_s3
        {
            "reasoning": 1,
            "content": 1,
            "_id": 0,
        },  # Project only reasoning and content fields
    )
    results = {doc["reasoning"]: doc["content"] for doc in documents}

    prompt = results.get(reasoning, "Not found")

    return prompt


def get_data_from_mongodb(
    client, dataset, sample_size=None, random_sample=False, **kwargs
):
    db = client[dataset]
    collection = db["context"]

    query = {}
    if "from_index" in kwargs:
        query["q_num"] = {"$gte": kwargs["from_index"]}


    if random_sample:
        data = list(collection.find(query))
        if sample_size and sample_size < len(data):
            return random.sample(data, sample_size)
        return data

    if sample_size:
        return list(collection.find(query).limit(sample_size))

    return list(collection.find(query))


def send_gemini_request(model, prompt):

    prompt_parts = [prompt]
    # print(f"Sending request to Gemini model with prompt: {prompt_parts}")
    retry_count = 0

    while retry_count < MAX_RETRY:
        try:
            response = model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            # print(f"Error: {e}")
            logger.error(f"send_gemini_request failed (Attempt {retry_count+1}): {e}")
            logger.debug(traceback.format_exc())
            time.sleep(RETRY_DELAY)
            retry_count += 1

    return None

def get_llama_client(api_key):
    """
    Creates a client for the Llama model using DeepInfra API.
    The client mimics the interface of the Gemini client for compatibility.
    """
    class LlamaClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            # DeepInfra endpoint for Llama
            self.base_url = "https://api.deepinfra.com/v1/inference"
            # Updated to the correct model ID

            self.model_id = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'
            # "meta-llama/Llama-4-Maverick-17B-128E-Instruct-Turbo"

        
        def generate_content(self, prompt_parts):
            """
            Generate content using the DeepInfra API for Llama model.
            This mimics the Gemini client's generate_content method.
            """
            url = f"{self.base_url}/{self.model_id}"
            
            # Handle prompt parts (which could be a list or a string)
            user_prompt = prompt_parts[0] if isinstance(prompt_parts, list) else prompt_parts
            
            # Format according to the correct Llama-4-Maverick format
            formatted_prompt = f"<|begin_of_text|><|header_start|>user<|header_end|>\n\n{user_prompt}<|eot|><|header_start|>assistant<|header_end|>\n\n"
            
            # Prepare the payload for DeepInfra API using the exact format from the curl command
            payload = {
                "input": formatted_prompt,
                "stop": [
                    "<|eot_id|>",
                    "<|end_of_text|>",
                    "<|eom_id|>"
                ]
            }
            
            try:
                print(f"Sending request to DeepInfra for Llama model...")
                response = requests.post(
                    url, 
                    headers=self.headers,
                    json=payload,


                    timeout=60  # Increased timeout for large models
                )
                
                if response.status_code != 200:
                    print(f"Error response: {response.status_code}")
                    print(f"Error content: {response.text}")
                
                response.raise_for_status()
                
                # Parse the response from DeepInfra
                result = response.json()
                response_text = result.get("results", [{}])[0].get("generated_text", "")
                
                # Create a response object with a text property similar to Gemini's response
                class TextResponse:
                    def __init__(self, text):
                        self.text = text
                
                return TextResponse(response_text)
                
            except requests.exceptions.RequestException as e:

                # print(f"DeepInfra API error: {str(e)}")
                logger.error(f"DeepInfra API error: {e}")
                logger.debug(traceback.format_exc())
                if hasattr(e, 'response') and e.response:
                    # print(f"Status code: {e.response.status_code}")
                    # print(f"Response body: {e.response.text}")
                    logger.error(f"Status code: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")

                # Return an error message instead of raising the exception
                # This allows the code to continue even if one request fails
                class TextResponse:
                    def __init__(self, text):
                        self.text = text
                return TextResponse(f"Error calling Llama API: {str(e)}")
    
    return LlamaClient(api_key)

def send_gpt_request(client, prompt, step=None):

    system_content = "You are a helpful assistant"
    # print("hello")
    retry_count = 0

    MODEL = "gpt-4o-mini"

    while retry_count < MAX_RETRY:
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            # print(f"Error: {e}")
            logger.error(f"send_gpt_request failed (Attempt {retry_count+1}): {e}")
            logger.debug(traceback.format_exc())
            time.sleep(RETRY_DELAY)
            retry_count += 1

    return None

#TODO : define the placeholder for the prompt
def prompt_request(model, model_name, prompt, table, question, text=None):
    print("Processing prompt request...")

    prompt = prompt.format(table=table, question=question)

    if model_name == "gemini":
        return send_gemini_request(model, prompt)
    elif model_name == "gpt-4o-mini":
        return send_gpt_request(model, prompt, "s1")
    elif model_name == "llama3-70b":
        return send_gemini_request(model, prompt)  # We can reuse this since our LlamaClient has the same interface
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def process_prompt(args):
    doc, model_name, reasoning, prompt, model = args
    print(f"Processing document with q_num: {doc['q_num']}")

    logger.info(f"Processing document with q_num: {doc.get('q_num', 'unknown')}")

    # print(doc)
    # print(doc, model_name, reasoning, prompt)
    try:
        required_fields = ["q_num", "table_id", "question", "table", "answer"]
        # print("Required fields: gotten")
        for field in required_fields:
            if field not in doc:
                raise KeyError(f"Required field '{field}' not found in doc")

        response = prompt_request(
            model, model_name, prompt, doc["table"], doc["question"]
        )
        print(response)

        logger.debug(f"Model response: {response}")


        return {
            "q_num": doc["q_num"],
            "reasoning": reasoning,
            "table_id": doc["table_id"],
            "question": doc["question"],
            "response": response,
            "answer": doc["answer"],
        }
    
    except:
        print("error in processing prompt")

        logger.exception(f"Error in process_prompt: {e}")



def update_mongodb(client, model_name, dataset, reasoning_type, results):
    db = client[dataset]
    collection = db[reasoning_type.lower()]

    operations = []

    for result in results:
        update_data = {**result, "evaluated": False}
        # print(update_data)
        # print(reasoning_type.lower())
        operations.append(
            UpdateOne(
                {
                    "q_num": result["q_num"],
                    "model": f"{model_name}",
                    "reasoning_type": reasoning_type.lower(),
                },
                {"$set": update_data},
                upsert=True,
            )
        )
    if operations:
        result = collection.bulk_write(operations)
        print("modified", result.modified_count)


def run_qa(
    dataset,
    model_name,
    reasoning,
    sample_size=None,
    random_sample=False,
    max_workers=1,
    **kwargs,
):
    load_dotenv()

    model = None

    if model_name == "gemini":
        model = get_gemini(google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif model_name == "gpt-4o-mini":
        model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif model_name == "llama3-70b":
        model = get_llama_client(api_key=os.getenv("LLAMA_API_KEY"))

    print(model_name)
    mongo_client = get_mongodb_client()
    data = get_data_from_mongodb(
        mongo_client, dataset, sample_size, random_sample, **kwargs
    )
    prompt = get_prompts_from_mongodb(mongo_client, dataset, reasoning, **kwargs)

    if model_name in ["gemini", "gpt-4o-mini", "llama3-70b"]:
        print(f"Retrieved {len(data)} documents")

        if data:
            print("Sample document:", len(data))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for doc in data:
                args = (doc, model_name, reasoning, prompt, model)
                futures.append(executor.submit(process_prompt, args))

            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc=f"Processing {reasoning} prompts",
            ):
                result = future.result()
                if result:
                    results.append(result)
        print(len(results))
    else:
        results = perform_batch_request(
            model_name, dataset, data, prompt, reasoning, model
        )
        
    update_mongodb(mongo_client, model_name, dataset, reasoning.lower(), results)
    mongo_client.close()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate responses with reasoning methods"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemini", 
        choices=["gemini", "gpt-4o-mini", "llama3-70b"],
        help="Model name (gemini, gpt-4o-mini, or llama3-70b)"
    )
    parser.add_argument("--dataset", type=str, default="wiki", help="Dataset name")
    parser.add_argument("--reasoning", type=str, default="cot", help="Reasoning type") # NoT
    parser.add_argument(
        "--sample_size", type=int, default=None, help="Number of samples to process" # small size 
    )
    parser.add_argument(
        "--random_sample", action="store_true", help="Enable random sampling"
    )
    parser.add_argument("--from_index", type=int, default=0, help="Start from index")
    parser.add_argument(
        "--max_workers",
        type=int,
        default=7,
        help="Maximum number of concurrent workers",
    )

    args = parser.parse_args()
    run_qa(
        dataset=args.dataset,
        model_name=args.model,
        reasoning=args.reasoning,
        sample_size=args.sample_size,
        random_sample=args.random_sample,
        from_index=args.from_index,
        max_workers=args.max_workers,
    )