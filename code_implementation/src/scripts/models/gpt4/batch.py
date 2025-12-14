import asyncio
import json
import os
import time
import tempfile
import re
from datetime import datetime, timedelta
import argparse

from openai import OpenAI
from dotenv import load_dotenv

ALLOWED_MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']

def create_file(client, file, purpose):
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

def retrieve(client, batch_job, file_path):
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

    with open(file_path, 'wb') as file:
        file.write(result_content)

    print(f"Results written to {file_path}")

def modify_jsonl_file(input_file, output_file, new_model):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            data = json.loads(line)
            data['body']['model'] = new_model
            json.dump(data, outfile)
            outfile.write('\n')

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    print(f"Ensured directory exists: {directory}")

def get_model_directory(model):
    ft_model_pattern = r'^ft:gpt-4o-mini-\d{4}-\d{2}-\d{2}:cogcomp::\w+$'
    return 'gpt4omini-finetune' if re.match(ft_model_pattern, model) else model

def run_qa(dataset, reasoning, model):
    load_dotenv()

    print(f"Running batch job for {dataset} dataset and {reasoning} reasoning with model {model}")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    model_dir = get_model_directory(model)
    original_file_path = f"./data/prompts/{model_dir}/{dataset}/{reasoning}.jsonl"
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.jsonl') as temp_file:
        temp_file_path = temp_file.name
        
    # Modify the JSONL file
    modify_jsonl_file(original_file_path, temp_file_path, model)

    file = create_file(client, temp_file_path, "Batch job input file")

    batch_job = create_batch_request(client, file.id, "/v1/chat/completions", "24h", {"description": "Batch job for movie data"})

    res_file_path = f"./data/results/{model_dir}/{dataset}/{reasoning}.jsonl"
    
    # Ensure the directory exists before retrieving the results
    ensure_directory_exists(res_file_path)
    
    retrieve(client, batch_job, res_file_path)

    # Delete the temporary file
    os.unlink(temp_file_path)


def qa_main():
    parser = argparse.ArgumentParser(description='Run batch job for QA')
    parser.add_argument('--dataset', type=str, required=True, help='Dataset to run batch job on')
    parser.add_argument('--model', type=str, required=True, help='Model to use for the batch job')
    parser.add_argument('--reasoning', type=str, required=True, help='Reasoning to run batch job on')

    args = parser.parse_args()
    dataset = args.dataset
    model = args.model
    reasoning = args.reasoning

    # reasoning = ['COT', 'POT', 'Evidence', 'Faithful', 'Decomposition', 'meta']
    # for reason in reasoning:
    run_qa(dataset, reasoning, model)

if __name__ == '__main__':
    qa_main()