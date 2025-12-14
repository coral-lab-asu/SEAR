import os
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from loguru import logger
from dotenv import load_dotenv
import argparse
import utils
import concurrent.futures
from tqdm import tqdm
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi

SYS_PROMPT = '''You are an advanced AI assistant specialized in meta-reasoning and data analysis. Your role is to answer questions about tabular data using a structured, logical approach. Here are your key capabilities and instructions:

1. Analyze the given table data carefully, extracting all relevant information.
2. Use a step-by-step reasoning process to break down and solve complex problems.
3. When appropriate, write Python code to perform calculations or data manipulation.
4. Provide clear, concise explanations for each step of your reasoning process.
5. Format your final answer as "Final Answer: [Your answer here]"
6. Adapt your approach based on the complexity of the question - use simpler methods for straightforward queries and more detailed analysis for complex ones.
7. If the table or question is unclear, ask for clarification before proceeding.
8. Maintain a formal, instructional tone in your responses.
9. Do not make assumptions beyond the given data. If critical information is missing, state this in your response.
10. Be prepared to handle a wide range of table formats and subject matters.

Remember, your goal is to provide accurate, well-reasoned answers while clearly demonstrating your thought process. Good luck!'''

def get_mongodb_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def update_mongodb(client, dataset, reasoning_type, results):
    db = client[dataset]
    collection = db[reasoning_type.lower()]
    
    operations = []
    for result in results:
        operations.append(
            UpdateOne(
                {'q_num': result['index'], 'model': 'gemini', 'reasoning_type': reasoning_type.lower()},
                {'$set': {
                    'question': result['question'],
                    'answer': result['answer'],
                    'response': result['response'],
                }},
                upsert=True
            )
        )
    
    if operations:
        result = collection.bulk_write(operations)
        logger.info(f"Upserted {result.upserted_count} and modified {result.modified_count} documents in {dataset}.{reasoning_type.lower()} collection")

def process_prompt(args):
    index, table_id, prompt, answer, question, model, reasoning_type = args
    try:
        response = model.generate_content(prompt, 
                                          safety_settings={
                                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                            })
        return {
            'index': index,
            'table_id': table_id,
            'question': question,
            'response': str(response.text),
            'answer': answer
        }
    except Exception as e:
        logger.error(f"Error processing prompt at index {index}: {e}")
        return None

def run_qa(dataset, rows=30, from_index=0, max_workers=5):
    reasoning_types = ['COT', 'Decomposition', 'Evidence', 'POT', 'Faithful']

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    _ = logger.add(f"{dataset}_qa.log", format="{time} {level} {message}", level="DEBUG")

    mongo_client = get_mongodb_client()

    for reasoning_type in reasoning_types:
        index = from_index
        prompts = list(utils.get_prompts(dataset=dataset, reasoning=reasoning_type, run_all=True, from_index=from_index))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for table_id, prompt, answer, question in prompts:
                args = (index, table_id, prompt, answer, question, model, reasoning_type)
                futures.append(executor.submit(process_prompt, args))
                index += 1

            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc=f"Processing {reasoning_type}"):
                result = future.result()
                if result:
                    results.append(result)

        update_mongodb(mongo_client, dataset, reasoning_type, results)

    mongo_client.close()
    logger.remove()
    return True

def process_meta_prompt(args):
    index, table_id, prompt, answer, question, model = args
    try:
        response = model.generate_content(prompt, 
                                          safety_settings={
                                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                            })
        return {
            'index': index,
            'table_id': table_id,
            'question': question,
            'response': str(response.text),
            'answer': answer
        }
    except Exception as e:
        logger.error(f"Error querying API at index {index}: {e}")
        return None

AGENT_SYS_PROMPT = '''Your task is to form concise instructions of steps following the guidelines presented below. You should guide, step-by-step, to another language model to arrive at a solution. 
                    The below guidelines are general and vague and contain the possible paths to take. 
                    Your instructions should be concise, and specific to the table and the question, and must instruct the model to exactly perform a sequence of steps to arrive at a solution. 
                    Do not give the answer, but only form a specific set of instructions to arrive at the answer. 
                    
                    Guidelines - '''

#def prompt_agent(dataset, reasoning, max_workers=5, **kwargs):


def run_meta_qa(dataset, reasoning, max_workers=5, **kwargs):
    _ = logger.add(f"{dataset}__META_qa.log", format="{time} {level} {message}", level="DEBUG")

    meta = kwargs.get('meta', False)
    reasoning_type = "meta" if meta else reasoning
    #print("What happened here?")

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    #print("the fucking API")

    prompts = list(utils.get_prompts(dataset, reasoning=reasoning, **kwargs))
    #print(prompts)

    mongo_client = get_mongodb_client()
    

    results = []
    #print(f"Processing {len(prompts)} prompts for {dataset} dataset and {reasoning_type} reasoning")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for index, (table_id, prompt, answer, question) in enumerate(prompts):
            args = (index, table_id, prompt, answer, question, model)
            futures.append(executor.submit(process_meta_prompt, args))

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing prompts"):
            result = future.result()
            if result:
                print(result)
                results.append(result)

    update_mongodb(mongo_client, dataset, reasoning_type, results)

    mongo_client.close()
    logger.remove()
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate prompts with meta template')
    parser.add_argument('--dataset', type=str, default='fetaqa', help='Dataset name')
    parser.add_argument('--reasoning', type=str, default='COT', help='Reasoning type')
    parser.add_argument('--rows', type=int, default=5000, help='Number of rows to generate')
    parser.add_argument('--random', type=bool, default=False, help='Generate random rows')
    parser.add_argument('--meta', type=bool, default=False, help='Generate meta prompts')
    parser.add_argument('--from_index', type=int, default=0, help='Start from index')
    parser.add_argument('--max_workers', type=int, default=5, help='Maximum number of concurrent workers')

    args = parser.parse_args()
    run_meta_qa(dataset=args.dataset, reasoning=args.reasoning, rows=args.rows, random=args.random, 
                from_index=args.from_index, meta=args.meta, max_workers=args.max_workers)