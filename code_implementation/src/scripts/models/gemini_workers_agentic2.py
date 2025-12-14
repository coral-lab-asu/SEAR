import os
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from loguru import logger
from dotenv import load_dotenv
import argparse
import concurrent.futures
from tqdm import tqdm
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi
import random

AGENT_SYS_PROMPT = '''Your task is to form concise instructions of steps following the guidelines presented below.
                    You should understand the task, the table, and the question. 
                    From the given guidelines, think step by step and analyze the table data carefully.
                    Once you perform your analysis, you should guide step-by-step, to another language model to arrive at a solution.
                    You should NEVER give the answer. Your task is only to generate clear instructions.
                    If anything is assumed in the question, your job is to make it clear in your instructions.
                    The below guidelines given to you are general and vague and contain the possible paths to take. 
                    Your instructions should be concise, and specific to the table and the question, and must instruct the model to exactly perform a sequence of steps to arrive at a solution. 
                    Do not give the answer, but only form a specific set of instructions to arrive at the answer. 
                    
                    Guidelines - '''

SYS_PROMPT = '''You are an advanced AI assistant specialized in analyzing tabular data and answering questions. Your role is to follow the given instructions carefully and provide accurate answers. Here are your key responsibilities:

1. Carefully read and follow the provided instructions step by step.
2. Analyze the given table data thoroughly, extracting all relevant information.
3. Perform any necessary calculations or data manipulations as instructed.
4. Provide clear explanations for each step of your reasoning process.
5. Draw logical conclusions based on the data and instructions.
6. Format your final answer as "Final Answer: [Your answer here]"
7. If any step is unclear or if critical information is missing, state this in your response.
8. Maintain a formal, analytical tone in your responses.

Your goal is to provide accurate, well-reasoned answers while clearly demonstrating your thought process and adhering to the given instructions.'''

def get_mongodb_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def update_mongodb(client, dataset, reasoning_type, results):
    db = client[dataset]
    collection = db[reasoning_type.lower()]
    
    operations = []
    
    for result in results:

        update_data = {**result, 'evaluated': False}

        operations.append(
            UpdateOne(
                {'q_num': result['q_num'], 'model': 'gemini-agent', 'reasoning_type': reasoning_type.lower()},
                {'$set': update_data},
                upsert=True
            )
        )
    
    if operations:
        result = collection.bulk_write(operations)
        logger.info(f"Upserted {result.upserted_count} and modified {result.modified_count} documents in {dataset}.{reasoning_type.lower()} collection")

def run_gemini(model, prompt):
    try:
        response = model.generate_content(prompt)
        return str(response.text)
    except Exception as e:
        logger.error(f"Error querying Gemini API: {e}")
        return None

def prompt_agent(agent_model, table, question, meta_prompt):
    meta_prompt = meta_prompt.format(context=table, question=question)
    prompt = f"{meta_prompt}\nInstructions:"
    logger.debug(f"Agent Prompt: {prompt}")
    return run_gemini(agent_model, prompt)

def process_prompt(args):
    doc, meta_prompt, agent_model, answer_model = args
    try:
        required_fields = ['q_num', 'table_id', 'question', 'table', 'answer']
        for field in required_fields:
            if field not in doc:
                raise KeyError(f"Required field '{field}' not found in document")

        logger.debug(f"Meta prompt: {meta_prompt}")
        logger.debug(f"Document: {doc}")
        # print(f"Document: {doc}")

        instructions = prompt_agent(agent_model, doc['table'], doc['question'], meta_prompt)

        if not instructions:
            logger.error("Failed to generate instructions")
            return None

        final_prompt = f"Instructions: {instructions}\n\nContext:\n{doc['table']}\n\nQuestion: {doc['question']}\n\nAnswer:"
        logger.debug(f"Final Prompt: {final_prompt}")
        
        final_response = run_gemini(answer_model, final_prompt)
        logger.debug(f"Final Response: {final_response}")

        return {
            'q_num': doc['q_num'],
            'table_id': doc['table_id'],
            'question': doc['question'],
            'response': final_response,
            'answer': doc['answer']
        }
    except Exception as e:
        logger.error(f"Error processing prompt for q_num {doc.get('q_num', 'Unknown')}: {e}")
        logger.exception("Full traceback:")
    return None

def get_data_from_mongodb(client, dataset, sample_size=None, random_sample=False, **kwargs):
    db = client[dataset]
    collection = db['context']
    
    query = {}
    if 'from_index' in kwargs:
        query['q_num'] = {'$gte': kwargs['from_index']}
    
    if random_sample:
        data = list(collection.find(query))
        if sample_size and sample_size < len(data):
            return random.sample(data, sample_size)
        return data
    
    if sample_size:
        return list(collection.find(query).limit(sample_size))
    
    return list(collection.find(query))

def get_prompt_from_mongodb(client, dataset, reasoning):
    db = client[dataset]
    collection = db['prompts']

    if reasoning.lower() != 'meta':
        print("Agentic Instruction is only for meta reasoning")
        exit(1)
    
    doc = collection.find_one({'reasoning': reasoning})
    if doc and 'content' in doc:
        return doc['content']
    else:
        logger.error(f"No prompt template found for reasoning: {reasoning}")
        return None

def run_qa(dataset, reasoning, sample_size=None, random_sample=False, max_workers=5, **kwargs):
    _ = logger.add(f"{dataset}__{reasoning}_qa.log", format="{time} {level} {message}", level="DEBUG")

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    agent_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=AGENT_SYS_PROMPT)
    answer_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYS_PROMPT)

    mongo_client = get_mongodb_client()
    data = get_data_from_mongodb(mongo_client, dataset, sample_size, random_sample, **kwargs)

    print(f'Retrieved {len(data)} documents')

    if data:
        print('Sample document:', data[0])

    meta_prompt = get_prompt_from_mongodb(mongo_client, dataset, reasoning)

    if not meta_prompt:
        logger.error(f"No prompt template found for reasoning: {reasoning}")
        return False

    logger.info(f"Meta prompt: {meta_prompt}")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for doc in data:
            args = (doc, meta_prompt, agent_model, answer_model)
            futures.append(executor.submit(process_prompt, args))

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc=f"Processing {reasoning} prompts"):
            result = future.result()
            if result:
                results.append(result)

    update_mongodb(mongo_client, dataset, reasoning.lower(), results)

    mongo_client.close()
    logger.remove()
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate responses with various reasoning methods')
    parser.add_argument('--dataset', type=str, default='fetaqa', help='Dataset name')
    parser.add_argument('--reasoning', type=str, default='COT', help='Reasoning type')
    parser.add_argument('--sample_size', type=int, default=None, help='Number of samples to process')
    parser.add_argument('--random_sample', action='store_true', help='Enable random sampling')
    parser.add_argument('--from_index', type=int, default=0, help='Start from index')
    parser.add_argument('--max_workers', type=int, default=5, help='Maximum number of concurrent workers')

    args = parser.parse_args()
    run_qa(dataset=args.dataset, reasoning=args.reasoning, sample_size=args.sample_size, 
           random_sample=args.random_sample, from_index=args.from_index, max_workers=args.max_workers)