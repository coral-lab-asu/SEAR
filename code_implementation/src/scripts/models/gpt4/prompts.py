import re
import os
import json
import argparse
from tqdm import tqdm
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

def get_mongodb_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def fetch_from_mongodb(collection, query):
    try:
        docs = collection.find(query)
        return list(docs)
    except Exception as e:
        print(f"Error fetching data from MongoDB: {e}")
        return None

def get_prompt(collection, reasoning):
    
    query = {'reasoning': reasoning}
    
    prompt = fetch_from_mongodb(collection, query)[0]
    print(prompt)
    
    if not prompt:
        print(f"Prompt not found for reasoning: {reasoning}")
        return None
    
    if prompt.get('system') is None or prompt.get('user') is None:
        
        if prompt.get('content') is None:
            print(f"Prompt content not found for reasoning: {reasoning}")
            return None
        
        return {'system': '', 'user': prompt['content']}
    
    return {'system': prompt['system'], 'user': prompt['user']}

def get_context(collection):
    query = {}
    context = fetch_from_mongodb(collection, query)
    for con in context:
        yield con['q_num'], con['table'], con['question']

def create_prompt_file(model, client, dataset, reasoning):
    prompt_collection = client[dataset]['prompts']
    prompt = get_prompt(prompt_collection, reasoning)

    tasks = []
    context_collection = client[dataset]['context']

    for q_num, table, question in get_context(context_collection):
        user_content = prompt['user'].format(context=table, question=question)
        system_content = prompt['system']

        task = {
            "custom_id": f"{q_num}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
            }
        }

        tasks.append(task)

    # Regex to identify fine-tuned models
    ft_model_pattern = r'^ft:gpt-4o-mini-\d{4}-\d{2}-\d{2}:cogcomp::\w+$'
    
    # Determine the model name for directory creation
    model_dir = 'gpt4omini-finetune' if re.match(ft_model_pattern, model) else model

    # Create directory structure
    base_dir = "./data/prompts"
    model_dataset_dir = os.path.join(base_dir, model_dir, dataset)
    os.makedirs(model_dataset_dir, exist_ok=True)

    # Save the file
    file_name = os.path.join(model_dataset_dir, f"{reasoning}.jsonl")

    with open(file_name, 'w+') as file:
        for obj in tasks:
            file.write(json.dumps(obj) + '\n')

if __name__ == '__main__':
    
    #Use reasoning = meta-finetune to get the finetuning prompt
    client = get_mongodb_client()
    
    parser = argparse.ArgumentParser(description='Load dataset for finetuning the model')
    parser.add_argument('--dataset', type=str, help='Name of the dataset to load')
    parser.add_argument('--reasoning', type=str, help='Reasoning path to load')
    parser.add_argument('--model', type=str, help='Model to use for the prompt')

    args = parser.parse_args()

    create_prompt_file(args.model, client, args.dataset, args.reasoning)