import sys
import json
import os
import argparse
import random
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from bson import json_util

def get_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def fetch(collection, query):
    documents = collection.find(query)
    return list(documents)

def fetch_context(collection, q_num):
    document = collection.find_one({'q_num': q_num})
    return document

def create_jsonl_data(meta_documents, system_content, user_prompt, context_collection):
    jsonl_data = []
    for doc in meta_documents:
        q_num = doc['q_num']
        context_doc = fetch_context(context_collection, q_num)

        if not context_doc:
            print(f"Warning: No context found for q_num {q_num}")
            continue

        user_content = user_prompt.format(
            context=context_doc.get('table', ''),
            question=context_doc.get('question', '')
        )

        # Check if 'response_ideal' exists, if not use 'response'
        response = doc.get('response_ideal') or doc.get('response')
        
        if not response:
            print(f"Warning: No response found for q_num {q_num}")
            continue

        # Check if 'reasoning_path' exists
        reasoning_path = doc.get('reasoning_paths', '')
        
        combined_content = f"Reasoning Path Chosen: {reasoning_path}\n{response}"

        jsonl_entry = {
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": combined_content}
            ]
        }

        jsonl_data.append(jsonl_entry)

    return jsonl_data

def write_jsonl_file(data, filename):

    shuffled_data = random.sample(data, len(data))
    
    with open(filename, 'w') as f:
        for entry in shuffled_data:
            json.dump(entry, f, default=json_util.default)
            f.write('\n')

def split_data(data, train_ratio=0.9):
    random.shuffle(data)
    split_index = int(len(data) * train_ratio)
    return data[:split_index], data[split_index:]

def main():
    parser = argparse.ArgumentParser(description='Load dataset for finetuning the model')
    parser.add_argument('--dataset', type=str, help='Name of the dataset to load')
    args = parser.parse_args()

    if not args.dataset:
        print("Usage: python script.py --dataset <dataset_name>")
        sys.exit(1)

    db = get_client()[args.dataset]

    finetune_query = {'model': 'gpt4o', 'finetune': True}
    meta_documents = fetch(db['meta'], finetune_query)

    system_prompt = fetch(db['prompts'], {'reasoning': 'meta-finetune'})[0]['system']
    user_prompt = fetch(db['prompts'], {'reasoning': "meta-finetune"})[0]['user']

    print(system_prompt)

    if not system_prompt or not user_prompt:
        print("Error: Could not fetch system or user content from prompts collection.")
        sys.exit(1)

    jsonl_data = create_jsonl_data(meta_documents, system_prompt, user_prompt, db['context'])
    
    train_data, test_data = split_data(jsonl_data)

    dataset_dir = f'./data/{args.dataset}'
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    write_jsonl_file(train_data, os.path.join(dataset_dir, 'train.jsonl'))
    write_jsonl_file(test_data, os.path.join(dataset_dir, 'validation.jsonl'))

    print(f"Train-Test split created successfully.")
    print(f"Train set: {len(train_data)} samples")
    print(f"Test set: {len(test_data)} samples")
    print("Files 'train.jsonl' and 'test.jsonl' have been created.")

if __name__ == "__main__":
    main()