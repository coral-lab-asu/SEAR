import os
import argparse
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from tqdm import tqdm

def get_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

# Function to check if a response is correct
def is_response_correct(doc):
    gem_eval_code_output = doc.get('gem_eval_code_output', '').lower() if doc.get('gem_eval_code_output') else ''
    gem_eval_extracted_response = doc.get('gem_eval_extracted_response', '').lower() if doc.get('gem_eval_extracted_response') else ''
    #print(f"gem Extracted eval : {gem_eval_extracted_response}")
    #print(f"gem code eval : {gem_eval_extracted_response}")
    return 'yes' in gem_eval_code_output or 'yes' in gem_eval_extracted_response

def aggregate_responses_by_model(dataset, model_name):
    # Connect to MongoDB
    client = get_client()
    db = client[dataset]

    # Collections
    collections = ['cot', 'decomposition', 'meta', 'evidence', 'faithful', 'pot']
    context_collection = db['context']
    results_collection = db['results']

    # Get all unique q_nums from the context collection
    q_nums = context_collection.distinct('q_num')

    # Prepare bulk operations
    bulk_operations = []

    # Fetch context documents in one batch
    context_docs = list(context_collection.find({'q_num': {'$in': q_nums}}, {'q_num': 1, 'question': 1, 'answer': 1, 'table': 1}))

    # Create a dictionary for quick lookup
    context_dict = {doc['q_num']: doc for doc in context_docs}

    # Iterate over each q_num
    for q_num in tqdm(q_nums):
        # Initialize the document for this q_num
        result_doc = {
            'q_num': q_num,
            'question': context_dict.get(q_num, {}).get('question', 'N/A'),
            'answer': context_dict.get(q_num, {}).get('answer', 'N/A'),
            'context' : context_dict.get(q_num, {}).get('table', 'N/A'),
            'correct_methods': {},
            'meta_response': '',
            'model': model_name  # Add model name to the result document
        }

        # Iterate over each collection
        for collection_name in collections:
            collection = db[collection_name]

            # Use projection to only fetch necessary fields
            doc = collection.find_one(
                {'q_num': q_num, 'model': model_name},
                {'response': 1, 'gem_eval_code_output': 1, 'gem_eval_extracted_response': 1}
            )
            if not doc:
                continue

            # Check if the response is correct
            #print(f"\nFor reasoning {collection_name} and q_num : {q_num}........")
            if is_response_correct(doc):
                # Add the response to correct_methods
                result_doc['correct_methods'][collection_name] = doc.get('response', '') or 'No Response'
                #print('Correct Response!!!!!!!!!!!!!\n')

            # Add the meta response specifically
            if collection_name == 'meta':
                result_doc['meta_response'] = doc.get('response', '') or 'No Meta Response'

        # Add the result document to the bulk operations
        bulk_operations.append(result_doc)

    # Execute bulk insert operation
    if bulk_operations:
        results_collection.insert_many(bulk_operations)

    # Confirm completion
    print(f"Aggregation completed for model '{model_name}' and results stored in the 'results' collection.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV files to MongoDB")
    parser.add_argument("--dataset", help="Name of the dataset (will be used as database name)")
    parser.add_argument("--model", help="Name of the response model")
    args = parser.parse_args()

    # Example usage
    aggregate_responses_by_model(args.dataset, args.model)  



