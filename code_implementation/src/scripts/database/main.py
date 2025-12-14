from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

def get_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def fetch_data(dataset, reasoning=None, q_num=None, model=None):
    """
    Fetch data from MongoDB based on given parameters.
    
    :param dataset: Name of the dataset (database)
    :param reasoning: Reasoning type (collection name), optional
    :param q_num: Question number, optional
    :param model: Model name, optional
    :return: List of documents matching the criteria
    """
    client = get_client()
    db = client[dataset]
    
    query = {}
    if model:
        query['model'] = model
    if q_num is not None:
        query['q_num'] = int(q_num)
    
    try:
        if reasoning:
            collection = db[reasoning]
            results = list(collection.find(query))
        else:
            results = []
            for collection_name in db.list_collection_names():
                collection = db[collection_name]
                results.extend(list(collection.find(query)))
        
        return results
    
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return []
    
    finally:
        client.close()

def update_document(dataset, reasoning, q_num, model, update_data):
    """
    Update a specific document in MongoDB.
    
    :param dataset: Name of the dataset (database)
    :param reasoning: Reasoning type (collection name)
    :param q_num: Question number
    :param model: Model name
    :param update_data: Dictionary containing fields to update
    :return: Update result
    """
    client = get_client()
    db = client[dataset]
    collection = db[reasoning]
    
    query = {'q_num': int(q_num), 'model': model}
    
    # Prepare update document
    update_doc = {"$set": {}}
    
    # Map of allowed fields and their types
    allowed_fields = {
        'question': str,
        'answer': str,
        'response': str,
        'extracted_response': str,
        'code_output': str,
        'f1_score_extracted_response': float,
        'f1_score_code_output': float,
        'f1_final': float,
        'gem_eval_extracted_response': str,
        'gem_eval_code_output': str,
        'gpt_eval_extracted_response': str,
        'gpt_eval_code_output': str,
        'gem_final': float,
        'eval_prompt': str,
        'tag': str,
        'notes': str
    }
    
    try:
        for field, value in update_data.items():
            if field in allowed_fields:
                # Convert the value to the correct type
                typed_value = allowed_fields[field](value)
                update_doc["$set"][field] = typed_value
            else:
                print(f"Warning: Field '{field}' is not allowed and will be ignored.")
        
        result = collection.update_one(query, update_doc)
        return result
    
    except Exception as e:
        print(f"An error occurred while updating the document: {e}")
        return None
    
    finally:
        client.close()

# Example usage:
if __name__ == "__main__":
    # Fetch data example
    results = fetch_data(dataset="fetaqa", reasoning="cot", q_num=1, model="gemini")
    for doc in results:
        print(doc)
    
    # Update document example
    update_result = update_document(
        dataset="fetaqa",
        reasoning="cot",
        q_num=9999,
        model="gemini",
        update_data={
            "f1_score_extracted_response": 0.85,
            "notes": "Updated response score"
        }
    )
    if update_result:
        print(f"Modified {update_result.modified_count} document(s)")