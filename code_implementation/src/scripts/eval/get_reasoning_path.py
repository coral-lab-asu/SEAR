import analyze
import pymongo
from pymongo.errors import BulkWriteError
import argparse


# Function to classify responses based on keywords
def classify_response(response):
    classification_keywords = {
        "COT": ["step-by-step", "logically", "each step or stage"],
        "Evidence Extraction": [
            "extract",
            "relevant information",
            "necessary data",
            "Extract Evidence",
        ],
        "Decomposition": ["decompose", "sub-problems", "break down", "Sub-problems"],
        "POT": [
            "single Python program",
            "unified Python script",
            "python",
            "print",
            "# Done",
        ],
        "F-COT": ["individual Python program", "separate Python scripts"],
        "NoT": [
            "class PlayerRolesTimeline",
            "get_narrative",
            "event_",
            "timeline",
            "narrative of thoughts",
            "storyline",
            "character",
            "timeline",
        ],
        "Tot": [
            "Tree of Thoughts",
            "ToT",
            "thoughts",
            "iterative thought generation",
            "evaluate intermediate thoughts",
        ],
        "GoT": [
            "Graph of Thoughts",
            "GoT",
            "graph",
            "nodes",
            "edges",
            "connections",
            "relationships",
        ],
        "SCP": [
            "Single Chain of Thought",
            "SCP",
            "single chain",
            "linear reasoning",
            "sequential steps",
        ],
        "Clear": [
            "clear",
            "reset",
            "initialize",
            "start over",
        ]
    }
    classifications = []
    response = response.lower() if response != None else ""
    for classification, keywords in classification_keywords.items():
        if any(keyword.lower() in response for keyword in keywords):
            classifications.append(classification)
    return ", ".join(classifications)


# Function to replace Decomposition and POT with F-COT if both are present
def replace_decomposition_pot_with_fcot(classification):
    classes = classification.split(", ")
    if "Decomposition" in classes and "POT" in classes:
        classes = [cls for cls in classes if cls not in ["Decomposition", "POT"]]
        classes.append("F-COT")
    return ", ".join(classes)


def update_documents_for_model(model_name, collection):
    # Query to find all documents with the specified model
    query = {"model": model_name}

    # Projection to include only necessary fields
    projection = {"q_num": 1, "response": 1}

    # Fetch documents corresponding to the model
    documents = list(collection.find(query, projection))

    # List to store update operations
    updates = []

    # Process each document
    for doc in documents:
        response_value = doc.get("response")
        reasoning_paths = classify_response(response_value)
        reasoning_paths = replace_decomposition_pot_with_fcot(reasoning_paths)

        # Prepare the update operation
        update_operation = {"q_num": doc["q_num"], "model": model_name}
        update = {"$set": {"reasoning_paths": reasoning_paths}}
        updates.append(
            pymongo.UpdateOne(update_operation, update, upsert=True),
        )

    # Perform bulk update
    if updates:
        try:
            result = collection.bulk_write(updates)
            print(f"Updated {result.modified_count} documents.")
        except BulkWriteError as bwe:
            print(f"Bulk write error: {bwe.details}")
    else:
        print("No documents to update.")


def get_reasoning_paths(dataset, model):
    client = analyze.get_client()
    db = client[dataset]
    collection = db["got"]

    update_documents_for_model(model, collection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV files to MongoDB")
    parser.add_argument(
        "--dataset", help="Name of the dataset (will be used as database name)"
    )
    parser.add_argument("--model", help="Name of the response model")
    args = parser.parse_args()

    # Example usage
    get_reasoning_paths(args.dataset, args.model)
