import os
import argparse
import json
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger
from openai import OpenAI
import time
from datetime import datetime, timedelta

# Gemini-specific functions
def process_prompt_gemini(args):
    model, prompt = args
    iteration = 0
    while(True):
        try:
            response = model.generate_content(
                prompt['body']['messages'][1]['content'],
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            return int(prompt['custom_id']), response.text
        except Exception as e:
            iteration += 1
            time.sleep(2)
            if(iteration==5):
                logger.error(f"Error processing prompt {prompt['custom_id']}: {e}")
                return int(prompt['custom_id']), None

# GPT-4 specific functions
def create_file(client, file, purpose=None):
    with open(file, 'rb') as file:
        return client.files.create(file=file, purpose='batch')

def create_batch_request(client, input_file_id, endpoint, completion_window, metadata):
    return client.batches.create(input_file_id=input_file_id, endpoint=endpoint, completion_window=completion_window, metadata=metadata)

def check_batch_status(client, batch_id):
    start_time = datetime.now()
    timeout = timedelta(hours=24)
    
    while datetime.now() - start_time < timeout:
        batch = client.batches.retrieve(batch_id)
        if batch.status == 'completed':
            return batch
        elif batch.status in ['failed', 'cancelled']:
            raise Exception(f"Batch failed or was cancelled. Status: {batch.status}")
        time.sleep(30)  # Check every 30s
    
    raise TimeoutError("Batch processing timed out after 24 hours")

def retrieve(client, batch_job):
    try:
        batch = check_batch_status(client, batch_job.id)
    except TimeoutError as e:
        print(f"Error: {e}")
        print("Attempting to cancel the batch...")
        client.batches.cancel(batch_job.id)
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    print(batch)
    result_file_id = batch.output_file_id
    result_content = client.files.content(result_file_id).content
    return result_content.decode('utf-8')

def get_mongodb_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def update_evaluation_results(mongo_client, dataset, response_model, reasoning, eval_results, evaluator):
    db = mongo_client[dataset]
    collection = db['meta'] if reasoning in ['meta', 'meta_co'] else db[reasoning]
    
    operations = []

    if reasoning in ['meta_co', 'pot', 'faithful']:
        update_field = 'gem_eval_code_output' if evaluator == 'GEM' else 'gpt_eval_code_output'
        if reasoning == 'meta_co':
            reasoning = 'meta'
    else:
        update_field = 'gem_eval_extracted_response' if evaluator == 'GEM' else 'gpt_eval_extracted_response'
    
    existing_docs = {doc['q_num']: doc.get(update_field) 
                     for doc in collection.find(
                         {'model': response_model, 'reasoning_type': reasoning},
                         {'q_num': 1, update_field: 1}
                     )}
    
    new_docs = 0
    updated_docs = 0
    unchanged_docs = 0
    
    for q_num, result in eval_results.items():
        q_num = int(q_num)
        if q_num not in existing_docs:
            new_docs += 1
            operations.append(
                UpdateOne(
                    {'q_num': q_num, 'model': response_model, 'reasoning_type': reasoning},
                    {'$set': {update_field: result}},
                    upsert=True
                )
            )
        elif existing_docs[q_num] != result:
            updated_docs += 1
            
            operations.append(
                UpdateOne(
                    {'q_num': q_num, 'model': response_model, 'reasoning_type': reasoning},
                    {'$set': {update_field: result, 
                              'evaluated': True}
                              }
                )
            )
        else:
            unchanged_docs += 1
    
    if operations:
        result = collection.bulk_write(operations)
        print(f"Results for {dataset}.{reasoning} collection:")
        print(f"  New documents inserted: {new_docs}")
        print(f"  Existing documents updated: {updated_docs}")
        print(f"  Documents unchanged: {unchanged_docs}")
        print(f"  Total documents processed: {len(eval_results)}")
    else:
        print(f"No updates to perform for {dataset}.{reasoning}")

def run_gemini_eval(dataset, reasoning, response_model, max_workers=5):
    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    print(f"Using Gemini model for evaluation with {max_workers} workers")

    file_path = f'./prompts/{response_model}/{dataset}/{reasoning}.jsonl'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as file:
        prompts = [json.loads(line.strip()) for line in file]
    
    if len(prompts) == 0:
        print(f"No prompts found in {file_path}. Skipping evaluation.")
        return

    eval_results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_prompt = {executor.submit(process_prompt_gemini, (model, prompt)): prompt for prompt in prompts}
        for future in tqdm(as_completed(future_to_prompt), total=len(prompts), desc="Processing prompts"):
            prompt_id, response = future.result()
            eval_results[prompt_id] = response

    mongo_client = get_mongodb_client()
    update_evaluation_results(mongo_client, dataset, response_model, reasoning, eval_results, 'GEM')
    mongo_client.close()

def run_gpt4_eval(response_model, dataset, reasoning):
    load_dotenv()
    print(f"Running batch job for {dataset} dataset and {reasoning} reasoning")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    file_path = f"./prompts/{response_model}/{dataset}/{reasoning}.jsonl"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as file:
        prompts = [json.loads(line.strip()) for line in file]
    
    if len(prompts) == 0:
        print(f"No prompts found in {file_path}. Skipping evaluation.")
        return

    file = create_file(client, file_path, "Batch job input file")
    batch_job = create_batch_request(client, file.id, "/v1/chat/completions", "24h", {"description": "Batch job for evaluation"})
    result_content = retrieve(client, batch_job)
    
    eval_results = {}
    for line in result_content.split('\n'):
        if line.strip():
            data = json.loads(line)
            custom_id = int(data['custom_id'])
            content = data['response']['body']['choices'][0]['message']['content']
            eval_results[custom_id] = content

    mongo_client = get_mongodb_client()
    update_evaluation_results(mongo_client, dataset, response_model, reasoning, eval_results, 'GPT4')
    mongo_client.close()

def main():
    parser = argparse.ArgumentParser(description='Run evaluation on prompts from JSON files')
    parser.add_argument('--evaluator', type=str, required=True, choices=['gpt4', 'gemini'], help='Model to use for evaluation')
    parser.add_argument('--response_model', type=str, required=True, choices=['gpt4o', 'gpt4omini', 'gemini', 'gpt4omini-finetune'], help='Model response to evaluate')
    parser.add_argument('--dataset', type=str, required=True, help='Dataset name')
    parser.add_argument('--reasoning', nargs='+', required=True, choices=['cot', 'pot', 'decomposition', 'faithful', 'meta', 'evidence'], help='Reasoning methods to process')
    parser.add_argument('--max_workers', default=1, type=int, help='Maximum number of concurrent workers (for Gemini)')

    args = parser.parse_args()

    log_file = f'eval_{args.evaluator}_{args.dataset}.log'
    logger.add(log_file, rotation="500 MB")

    print(f"Running evaluation for {args.dataset} dataset using {args.evaluator} model for model response {args.response_model}")

    reasoning_types = args.reasoning
    if 'meta' in reasoning_types:
        reasoning_types.append('meta_co')

    for reasoning in reasoning_types:
        print(f"Processing {reasoning}")
        
        if args.evaluator == 'gpt4':
            run_gpt4_eval(args.response_model, args.dataset, reasoning)
        elif args.evaluator == 'gemini':
            run_gemini_eval(args.dataset, reasoning, args.response_model, args.max_workers)

if __name__ == '__main__':
    main()