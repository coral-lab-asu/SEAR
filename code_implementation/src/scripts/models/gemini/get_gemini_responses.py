import os
import json
import argparse
import tempfile  # Add this import
from pymongo import MongoClient, ASCENDING
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional
import threading
from tqdm import tqdm
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from openai import OpenAI


# Environment variable for MongoDB connection URI
MONGODB_URI = os.getenv("MONGODB_URI_BASELINES")

# Lock for MongoDB writes (if needed to prevent race conditions)
lock = threading.Lock()

# Function to check the batch job status
def check_batch_status(client, batch_id):
    start_time = datetime.now()
    timeout = timedelta(hours=24)
    
    while datetime.now() - start_time < timeout:
        batch = client.batches.retrieve(batch_id)
        if batch.status == 'completed':
            return batch
        elif batch.status in ['failed', 'cancelled']:
            raise Exception(f"Batch failed or was cancelled. Status: {batch.status}")
        else:
            print("Waiting for job to complete........")
        time.sleep(30)  # Check every 30 seconds
    
    raise TimeoutError("Batch processing timed out after 24 hours")

# Mock gemini model function for response generation
def gemini_response(prompt: str, model: Any) -> str:
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        return response.text
    except Exception as e:
        return str(e)


def get_gemini_model():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_gemini = genai.GenerativeModel('gemini-1.5-flash')
    return model_gemini

def process_document(doc, context_collection, prompts_collection, reasoning_collection, input_reasoning, model):
    # Extract relevant fields from the 'context' document
    q_num = doc.get('q_num')
    question = doc.get('question')
    table = doc.get('table')
    answer = doc.get('answer')
    
    # Get the prompt document based on reasoning
    prompt_doc = prompts_collection.find_one({'reasoning': input_reasoning})
    if not prompt_doc:
        raise ValueError(f"No prompt found for reasoning: {input_reasoning}")

    # Prepare prompt by replacing placeholders
    prompt = prompt_doc['content']
    prompt = prompt.replace("{context}", table).replace("{question}", question)
    
    # Generate response using the model
    response = gemini_response(prompt, model)
    
    # Prepare the new document to insert
    new_document = {
        'model': 'gemini',
        'reasoning_type': input_reasoning,
        'q_num': q_num,
        'question': question,
        'answer': answer,
        'response': response,
        'evaluated': False,
        'gem_eval_extracted_response': None,
        'gem_eval_code_output': None,
        'extracted_response': None,
    }

    # Insert or replace document in reasoning collection
    with lock:
        reasoning_collection.replace_one({'q_num': q_num}, new_document, upsert=True)

# Function to create a single batch request entry for gpt-4o-mini
def create_single_request(index, q_num, prompt):
    return {
        "custom_id": f"request-{index}-{q_num}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000
        }
    }

# Function to generate and submit batch requests for gpt-4o-mini
def process_gpt_4o_mini_batch(documents, prompts_collection, client, openai_client, input_reasoning):
    batch_requests = []
    qnum_map = {}  # Mapping of q_num to question and answer for later retrieval

    for index, doc in enumerate(documents):
        q_num = doc.get('q_num')
        question = doc.get('question')
        table = doc.get('table')
        answer = doc.get('answer')
        
        # Save question and answer for each q_num
        qnum_map[q_num] = {'question': question, 'answer': answer}
        
        # Get the prompt template from prompts collection
        prompt_doc = prompts_collection.find_one({'reasoning': input_reasoning})
        prompt = prompt_doc['content'].replace("{context}", table).replace("{question}", question)
        
        # Create and add batch request with q_num in custom_id
        batch_requests.append(create_single_request(index, q_num, prompt))
    
    # Save batch requests to JSON Lines format file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.jsonl') as temp_file:
        batch_file_path = temp_file.name
        with open(batch_file_path, 'w') as f:
            for request in batch_requests:
                f.write(json.dumps(request) + '\n')
    
    # Submit the batch to OpenAI
    batch_job = submit_batch_request(openai_client, batch_file_path)
    
    return batch_job, qnum_map

# Function to submit a batch request to OpenAI
def submit_batch_request(openai_client, file_path):
    with open(file_path, 'rb') as f:
        file = openai_client.files.create(file=f, purpose='batch')
    batch_job = openai_client.batches.create(input_file_id=file.id, endpoint='/v1/chat/completions', completion_window='24h', metadata={"description": "Batch job for context improvement"})
    print(f"GPT Batch job submitted with ID: {batch_job.id}")
    return batch_job

# Function to process responses from gpt-4o-mini
def map_responses_to_documents(batch_job, reasoning_collection, qnum_map, openai_client, input_reasoning):
    batch = check_batch_status(openai_client, batch_job.id)
    
    # Retrieve the response content
    result_file_id = batch.output_file_id
    result_content = openai_client.files.content(result_file_id).content.decode('utf-8')
    
    # Map responses to documents
    for line in result_content.splitlines():
        response_data = json.loads(line)
        custom_id = response_data['custom_id']
        q_num = int(custom_id.split('-')[-1])  # Extract q_num from custom_id
        response_content = response_data['response']['body']['choices'][0]['message']['content']
        
        # Retrieve original question and answer using q_num from qnum_map
        question = qnum_map[q_num]['question']
        answer = qnum_map[q_num]['answer']
        
        # Update or insert document in MongoDB
        new_document = {
            'model': 'gpt-4o-mini',
            'reasoning_type': input_reasoning,
            'q_num': q_num,
            'question': question,
            'answer': answer,
            'response': response_content,
            'evaluated': False,
            'gem_eval_extracted_response': None,
            'gem_eval_code_output': None,
            'extracted_response': None,
        }
        with lock:
            reasoning_collection.replace_one({'q_num': q_num}, new_document, upsert=True)



def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process MongoDB documents for Gemini model.")
    parser.add_argument('--dataset', type=str, help="The name of the MongoDB dataset.")
    parser.add_argument('--reasoning', type=str, help="The name of the reasoning type.")
    parser.add_argument('--model', type=str, help="The model to be used.")
    parser.add_argument('--documents', type=int, default=None, help="Number of documents to process.")
    args = parser.parse_args()
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[args.dataset]
    reasoning_collection = db[args.reasoning]
    prompts_collection = db["prompts"]
    context_collection = db["context"]

    # Retrieve documents
    documents = list(context_collection.find({}).sort("q_num", ASCENDING))
    if args.documents:
        documents = documents[:args.documents]

    if args.model == 'gemini':
        model = get_gemini_model()
        with tqdm(total=len(documents), desc="Processing documents") as progress_bar:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(process_document, doc, context_collection, prompts_collection, reasoning_collection, args.reasoning, model)
                    for doc in documents
                ]
                for future in as_completed(futures):
                    future.result()
                    progress_bar.update(1)

    elif args.model == 'gpt-4o-mini':
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        batch_job, qnum_map = process_gpt_4o_mini_batch(documents, prompts_collection, client, openai_client, args.reasoning)
        map_responses_to_documents(batch_job, reasoning_collection, qnum_map, openai_client, args.reasoning)

    client.close()

if __name__ == "__main__":
    main()