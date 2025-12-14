import os
import argparse
import json

import pandas as pd

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

import time
from datetime import datetime, timedelta

import glob

# Gemini-specific functions
def process_prompt_gemini(args):
    model, prompt = args
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
        logger.error(f"Error processing prompt {prompt['custom_id']}: {e}")
        return int(prompt['custom_id']), None

# GPT-4 specific functions
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

def save_evaluation_results(response_model, dataset, reasoning, input_file, eval_results, evaluator):
    output_file = f'./results/{response_model}/{dataset}/{reasoning}.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Read the existing CSV file if it exists, otherwise read the input file
    df = pd.read_csv(output_file) if os.path.exists(output_file) else pd.read_csv(input_file)
    df['index'] = df['index'].astype(int)
    df.set_index('index', inplace=True)

    df[evaluator] = pd.Series(eval_results)

    df.to_csv(output_file)
    
    print(f"Results saved to {output_file}")
    print(f"Number of rows in CSV: {len(df)}")
    print(f"Number of columns in CSV: {len(df.columns)}")
    print(f"Columns: {', '.join(df.columns)}")
    print(f"Number of evaluation results: {len(eval_results)}")

def run_gemini_eval(input_file, dataset, reasoning, response_model, max_workers=5):
    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")

    prompts = []
    with open(f'./prompts/{response_model}/{dataset}/{reasoning}.jsonl', 'r') as file:
        for line in file:
            prompts.append(json.loads(line.strip()))

    eval_results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_prompt = {executor.submit(process_prompt_gemini, (model, prompt)): prompt for prompt in prompts}
        for future in tqdm(as_completed(future_to_prompt), total=len(prompts), desc="Processing prompts"):
            prompt_id, response = future.result()
            eval_results[prompt_id] = response

    save_evaluation_results(response_model, dataset, reasoning, input_file, eval_results, 'GEM')

def run_gpt4_eval(response_model, response_path, dataset, reasoning):
    load_dotenv()

    print(f"Running batch job for {dataset} dataset and {reasoning} reasoning")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    file_path = f"./prompts/{response_model}/{dataset}/{reasoning}.jsonl"

    file = create_file(client, file_path, "Batch job input file")

    batch_job = create_batch_request(client, file.id, "/v1/chat/completions", "24h", {"description": "Batch job for evaluation"})

    os.makedirs(f"./results/{response_model}/{dataset}", exist_ok=True)
    res_file_path = f"./results/{response_model}/{dataset}/{reasoning}.jsonl"
    
    retrieve(client, batch_job, res_file_path)

    input_file = f'{response_path}/{reasoning}.csv'
    
    eval_results = {}
    with open(res_file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            custom_id = int(data['custom_id'])
            content = data['response']['body']['choices'][0]['message']['content']
            eval_results[custom_id] = content

    save_evaluation_results(response_model, dataset, reasoning, input_file, eval_results, 'GPT4')

def combine_csv_files(input_directory, output_file):
 
    all_files = glob.glob(os.path.join(input_directory, "*.csv"))
    
    dfs = []
    
    for file in all_files:
        df = pd.read_csv(file)
        
        filename = os.path.splitext(os.path.basename(file))[0]
        
        df = df[['index', 'question', 'answer', 'F1_score', 'GEM', 'GPT4']]
        df = df.rename(columns={
            'f1_score': f'F1_{filename}',
            'GEM': f'GEM_{filename}',
            'GPT4': f'GPT4_{filename}'
        })
        
        dfs.append(df)
    
    combined_df = pd.concat(dfs, axis=1)
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
    
    combined_df.to_csv(output_file, index=False)
    
    print(f"Combined CSV file saved to {output_file}")
    print(f"Number of rows: {len(combined_df)}")
    print(f"Number of columns: {len(combined_df.columns)}")
    print(f"Columns: {', '.join(combined_df.columns)}")

def main():

    parser = argparse.ArgumentParser(description='Run evaluation on prompts from JSON files')

    parser.add_argument('--responses', type=str, required=True, help='Path to the response CSV file or directory')
    parser.add_argument('--evaluator', type=str, required=True, choices=['gpt4', 'gemini'], help='Model to use for evaluation')
    parser.add_argument('--response_model', type=str, required=True, choices=['gpt4', 'gemini'], help='Model response to evaluate')
    parser.add_argument('--max_workers', default=10, type=int, help='Maximum number of concurrent workers (for Gemini)')

    args = parser.parse_args()

    # Set up logging
    log_file = f'eval_{args.evaluator}_{os.path.basename(args.responses)}.log'
    logger.add(log_file, rotation="500 MB")

    dataset = os.path.basename(args.responses)

    print(f"Running evaluation for {dataset} dataset using {args.evaluator} model for model response {args.response_model}")

    if args.evaluator == 'gpt4':
        for reasoning in os.listdir(args.responses):

            if reasoning.endswith('.csv'):

                reasoning = reasoning[:-4]  # Remove .csv extension

                #if reasoning.lower() not in ['pot', 'faithful']:
                run_gpt4_eval(args.response_model, args.responses, dataset, reasoning)

    elif args.evaluator == 'gemini':

        for reasoning in os.listdir(args.responses):

            if reasoning.endswith('.csv'):

                reasoning = reasoning[:-4]  # Remove .csv extension
                
                #if reasoning.lower() not in ['pot', 'faithful']:
                print(f"Processing {reasoning}")
                input_file = os.path.join(args.responses, reasoning + '.csv')
                run_gemini_eval(input_file, dataset, reasoning, args.response_model, args.max_workers)

if __name__ == '__main__':
    main()