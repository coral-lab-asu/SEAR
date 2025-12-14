import json
import re
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from tqdm import tqdm
import argparse

def get_mongodb_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    return data

def extract_responses(jsonl_data):
    responses = [(int(item['custom_id']), item['response']['body']['choices'][0]['message']['content']) for item in jsonl_data]
    #sort responses by custom_id
    responses.sort(key=lambda x: x[0])
    #print(responses)
    return responses

def fetch_existing_data(client, dataset, reasoning):
    db = client[dataset]
    collection = db[reasoning]
    return {doc['q_num']: doc for doc in collection.find({}, {'q_num': 1, 'question': 1, 'answer': 1})}

def insert_to_mongodb(client, dataset, reasoning, response_model, jsonl_responses, existing_data):
    db = client[dataset]
    collection = db[reasoning]

    column_mapping = {
        'index': 'q_num',
        'question': 'question',
        'answer': 'answer',
        'response': 'response',
        'output': 'extracted_response',
        'code_output': 'code_output',
        'f1_score': 'f1_score_extracted_response',
        'f1_score_code_output': 'f1_score_code_output',
        'f1_final': 'f1_final',
        'GEM': 'gem_eval_extracted_response',
        'gem_eval_code_output': 'gem_eval_code_output',
        'GPT4': 'gpt_eval_extracted_response',
        'gpt_eval_code_output': 'gpt_eval_code_output',
        'gem_final': 'gem_final',
        'gpt4_final': 'gpt4_final',
        'eval_prompt': 'eval_prompt',
        'tag': 'tag',
        'notes': 'notes'
    }

    operations = []
    for index, response in enumerate(jsonl_responses):
        #print("Index is:", response[0])
        existing_doc = existing_data.get(index, {})
        #print("Existing doc is: ", existing_doc)
        #print("Existing doc is: ", existing_doc)
        #print(index, response[1])
        document = {
            'model': response_model,
            'reasoning_type': reasoning,
            'q_num': index,
            'question': existing_doc.get('question'),
            'answer': existing_doc.get('answer'),
            'response': response[1],
            'evaluated': False,
            'gem_eval_extracted_response': None,
            'gem_eval_code_output': None,
            'extracted_response': None,
        }
        
        #print("Document is: ", document)

        operations.append(
            UpdateOne(
                {'q_num': response[0], 'model': response_model, 'reasoning_type': reasoning},
                {'$set': document},
                upsert=True
            )
        )

    if operations:
        result = collection.bulk_write(operations)
        print(f"Inserted/Updated {result.upserted_count + result.modified_count} documents in {dataset}.{reasoning} collection")

def get_model_directory(model):
    ft_model_pattern = r'^ft:gpt-4o-mini-\d{4}-\d{2}-\d{2}:cogcomp::\w+$'
    return 'gpt4omini-finetune' if re.match(ft_model_pattern, model) else model

def save(client, dataset, reasoning, response_model):
    model_dir = get_model_directory(response_model)
    jsonl_file_path = f'./data/results/{model_dir}/{dataset}/{reasoning}.jsonl'

    if reasoning == 'meta-finetune':
        #treat meta-finetune as meta for all operations
        reasoning = 'meta'
    
    jsonl_data = read_jsonl(jsonl_file_path)
    jsonl_responses = extract_responses(jsonl_data)
    
    existing_data = fetch_existing_data(client, dataset, reasoning)

    if response_model == 'gpt-4o-mini':
        response_model = 'gpt4omini'
    
    insert_to_mongodb(client, dataset, reasoning, response_model, jsonl_responses, existing_data)
    
    print(f"Data has been inserted into MongoDB for {dataset}.{reasoning}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process results and save to MongoDB')
    parser.add_argument('--datasets', type=str, help='Comma-separated list of datasets', 
                        choices=['fetaqa', 'finqa', 'sqa', 'hybridqa', 'tatqa', 'squall', 'hitabs', 'multi', 'wiki'])
    
    parser.add_argument('--response_model', type=str, help='Response model used')

    
    parser.add_argument('--reasonings', type=str, help='Comma-separated list of reasonings', 
                        choices=['pot', 'cot', 'faithful', 'decomposition', 'evidence', 'meta', 'meta-finetune'])

    args = parser.parse_args()

    datasets = args.datasets.split(',')
    response_model = args.response_model
    reasonings = args.reasonings.split(',')

    # Regex to identify fine-tuned models
    ft_model_pattern = r'^ft:gpt-4o-mini-\d{4}-\d{2}-\d{2}:cogcomp::\w+$'
    
    # Determine the model name for directory creation
    response_model = 'gpt4omini-finetune' if re.match(ft_model_pattern, response_model) else response_model

    
    client = get_mongodb_client()

    for dataset in datasets:
        for reasoning in reasonings:
            save(client, dataset, reasoning, response_model)

    client.close()