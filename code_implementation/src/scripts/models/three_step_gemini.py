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

from openai import OpenAI

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


from gpt_utils import *

# Add prompt to the system path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "three_prompts"))
)


MAX_RETRY = 5
RETRY_DELAY = 5


def get_mongodb_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI_3_STEPS")
    return MongoClient(uri, server_api=ServerApi("1"))


def get_prompts_from_mongodb(client, dataset, reasoning, **kwargs):
    db = client[dataset]
    collection = db["prompts"]
    s1 = ""
    s2 = ""
    s3 = ""

    if reasoning == "meta_3_step":
        s1 = "meta_s1"
        s2 = "meta_s2"
        s3 = "meta_s3"
    else:
        s1 = "clean_meta_s1"
        s2 = "clean_meta_s2"
        s3 = "clean_meta_s3"

    reasoning_values = [s1, s2, s3]
    print(reasoning_values)
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

    s1_prompt = results.get(s1, "Not found")
    s2_prompt = results.get(s2, "Not found")
    s3_prompt = results.get(s3, "Not found")

    # print(f"s1: {s1_prompt}")
    # print(f"s2: {s2_prompt}")
    # print(f"s3: {s3_prompt}")

    return [s1_prompt, s2_prompt, s3_prompt]


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
    retry_count = 0

    while retry_count < MAX_RETRY:
        try:
            response = model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(RETRY_DELAY)
            retry_count += 1

    return None


def send_gpt_request(client, prompt, step=None):
    if step == "s1":
        system_content = "You are a meta-selector tasked with constructing the most efficient pathway for solving tabular questions."
    else:
        system_content = "You are a helpful assistant"

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
            print(f"Error: {e}")
            time.sleep(RETRY_DELAY)
            retry_count += 1

    return None


def s1_prompt_request(model, model_name, prompt, table, question, text=None):
    s1_prompt = prompt.format(table=table, question=question)
    return (
        send_gemini_request(model, s1_prompt)
        if model_name == "gemini"
        else send_gpt_request(model, s1_prompt, "s1")
    )


def s2_prompt_request(
    model, model_name, prompt, table, question, crucial_steps, text=None
):
    s2_prompt = prompt.format(
        table=table, question=question, crucial_steps=crucial_steps
    )
    return (
        send_gemini_request(model, s2_prompt)
        if model_name == "gemini"
        else send_gpt_request(model, s2_prompt)
    )


def s3_prompt_request(
    model, model_name, prompt, table, question, detailed_steps, text=None
):
    s3_prompt = prompt.format(
        table=table, question=question, detailed_steps=detailed_steps
    )
    return (
        send_gemini_request(model, s3_prompt)
        if model_name == "gemini"
        else send_gpt_request(model, s3_prompt)
    )


def process_prompt(args):
    doc, model_name, reasoning, prompts, s1_model, s2_model, s3_model = args
    try:
        required_fields = ["q_num", "table_id", "question", "answer"]
        table_field = "table"
        if reasoning == "meta_3_step":
            required_fields.append("table")
        else:
            table_field = "improved_table_gpt4omini"
            required_fields.append("improved_table_gpt4omini")
        for field in required_fields:
            if field not in doc:
                raise KeyError(f"Required field '{field}' not found in doc")
        table_data = doc[table_field]
        # print(table_field)
        crucial_steps = s1_prompt_request(
            s1_model, model_name, prompts[0], table_data, doc["question"]
        )

        if crucial_steps == None:
            print("crucial steps error")
            return None

        detailed_steps = s2_prompt_request(
            s2_model,
            model_name,
            prompts[1],
            table_data,
            doc["question"],
            crucial_steps,
        )

        if detailed_steps == None:
            print("detailed steps error")
            return None

        answer = s3_prompt_request(
            s3_model,
            model_name,
            prompts[2],
            table_data,
            doc["question"],
            detailed_steps,
        )

        # print("Answer -- ", doc["answer"])

        return {
            "q_num": doc["q_num"],
            "reasoning": reasoning,
            "table_id": doc["table_id"],
            "question": doc["question"],
            "crucial_steps": crucial_steps,
            "detailed_steps": detailed_steps,
            "response": answer,
            "answer": doc["answer"],
        }
    except Exception as e:
        print(f"Some Error: {e}")


def update_mongodb(client, model_name, dataset, reasoning_type, results):
    db = client[dataset]
    collection = db[reasoning_type.lower()]

    operations = []

    print("Obtained Results for ", len(results))

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

    s1_model = None
    s2_model = None
    s3_model = None
    print(model_name)
    if model_name == "gemini":
        s1_model = get_gemini(google_api_key=os.getenv("GOOGLE_API_KEY"))

        s2_model = get_gemini(google_api_key=os.getenv("GOOGLE_API_KEY"))

        s3_model = get_gemini(google_api_key=os.getenv("GOOGLE_API_KEY"))

    if model_name == "gpt-4o-mini":
        s1_model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        s2_model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        s3_model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    mongo_client = get_mongodb_client()
    print("Connected to MonogoCompass!")
    data = get_data_from_mongodb(
        mongo_client, dataset, sample_size, random_sample, **kwargs
    )
    prompts = get_prompts_from_mongodb(mongo_client, dataset, reasoning, **kwargs)

    if model_name == "gemini" or model_name == "gpt-4o-mini":

        print(f"Retrieved {len(data)} documents")

        if data:
            print("Sample document:", len(data))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for doc in data:
                args = (
                    doc,
                    model_name,
                    reasoning,
                    prompts,
                    s1_model,
                    s2_model,
                    s3_model,
                )
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
            model_name, dataset, data, prompts, reasoning, s1_model, s2_model, s3_model
        )
    update_mongodb(mongo_client, model_name, dataset, reasoning.lower(), results)

    mongo_client.close()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate responses with 3 step reasoning methods"
    )
    parser.add_argument("--model", type=str, default="gemini", help="Model name")
    parser.add_argument("--dataset", type=str, default="wiki", help="Dataset name")
    parser.add_argument(
        "--reasoning", type=str, default="meta_3_step", help="Reasoning type"
    )
    parser.add_argument(
        "--sample_size", type=int, default=None, help="Number of samples to process"
    )
    parser.add_argument(
        "--random_sample", action="store_true", help="Enable random sampling"
    )
    parser.add_argument("--from_index", type=int, default=0, help="Start from index")
    parser.add_argument(
        "--max_workers",
        type=int,
        default=1,
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
