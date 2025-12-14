import os
import argparse
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from datetime import datetime

TOTAL_COUNTS = {
    "wiki": 1504,
    "multi": 1587,
    "hitabs": 897,
    "finqa": 962,
    "tatqa": 2244,
    "fetaqa": 1582,
    "sqa": 248,
    "squall": 774,
    "hybridqa": 1528,
}


def get_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    return MongoClient(uri, server_api=ServerApi("1"))


def process_collection(collection, model, evaluator, dataset):
    pipeline_llm_or_f1 = [
        {
            "$match": {
                "model": model,
                "$or": [
                    {f"{evaluator}_eval_extracted_response": {"$exists": True}},
                    {f"{evaluator}_eval_code_output": {"$exists": True}},
                ],
            }
        },
        {
            "$project": {
                "eval_result": {
                    "$cond": {
                        "if": {
                            "$or": [
                                {
                                    "$regexMatch": {
                                        "input": {
                                            "$ifNull": [
                                                f"${evaluator}_eval_extracted_response",
                                                "",
                                            ]
                                        },
                                        "regex": "yes",
                                        "options": "i",
                                    }
                                },
                                {
                                    "$regexMatch": {
                                        "input": {
                                            "$ifNull": [
                                                f"${evaluator}_eval_code_output",
                                                "",
                                            ]
                                        },
                                        "regex": "yes",
                                        "options": "i",
                                    }
                                },
                                {"$gt": ["$f1_final", 80]},
                            ]
                        },
                        "then": "yes",
                        "else": "no",
                    }
                }
            }
        },
        {"$group": {"_id": "$eval_result", "count": {"$sum": 1}}},
    ]

    pipeline_f1 = [
        {"$match": {"model": model, "f1_final": {"$exists": True, "$ne": None}}},
        {
            "$project": {
                "_id": 0,  # Exclude the document ID from the results
                "f1_final": 1,  # Include only the f1_final field in the results
            }
        },
    ]

    pipeline_llm = [
        {
            "$match": {
                "model": model,
                "$or": [
                    {f"{evaluator}_eval_extracted_response": {"$exists": True}},
                    {f"{evaluator}_eval_code_output": {"$exists": True}},
                ],
            }
        },
        {
            "$project": {
                "eval_result": {
                    "$cond": {
                        "if": {
                            "$or": [
                                {
                                    "$regexMatch": {
                                        "input": {
                                            "$ifNull": [
                                                f"${evaluator}_eval_extracted_response",
                                                "",
                                            ]
                                        },
                                        "regex": "yes",
                                        "options": "i",
                                    }
                                },
                                {
                                    "$regexMatch": {
                                        "input": {
                                            "$ifNull": [
                                                f"${evaluator}_eval_code_output",
                                                "",
                                            ]
                                        },
                                        "regex": "yes",
                                        "options": "i",
                                    }
                                },
                            ]
                        },
                        "then": "yes",
                        "else": "no",
                    }
                }
            }
        },
        {"$group": {"_id": "$eval_result", "count": {"$sum": 1}}},
    ]

    llm_or_f1_results = list(collection.aggregate(pipeline_llm_or_f1))
    f1_results = list(collection.aggregate(pipeline_f1))
    llm_results = list(collection.aggregate(pipeline_llm))

    # for item in f1_results:
    #     print(item)
    yes_count_llm_or_f1 = next(
        (item["count"] for item in llm_or_f1_results if item["_id"] == "yes"), 0
    )
    no_count_llm_or_f1 = next(
        (item["count"] for item in llm_or_f1_results if item["_id"] == "no"), 0
    )

    yes_count_llm = next(
        (item["count"] for item in llm_results if item["_id"] == "yes"), 0
    )
    no_count_llm = next(
        (item["count"] for item in llm_results if item["_id"] == "no"), 0
    )

    f1_score = 0
    for item in f1_results:
        f1_score += item["f1_final"]
    if (yes_count_llm_or_f1 + no_count_llm_or_f1) == 0 or (
        yes_count_llm + no_count_llm
    ) == 0:
        print("No responses try different model or dataset")
        return (0, 0), (0, 0), 0

    f1_score = (f1_score / TOTAL_COUNTS[dataset]) / 100

    return (
        (yes_count_llm_or_f1, no_count_llm_or_f1),
        (yes_count_llm, no_count_llm),
        f1_score,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Process evaluation results from MongoDB."
    )
    parser.add_argument("--model", help="The response model to evaluate")
    parser.add_argument(
        "--evaluator",
        choices=["gemini", "gpt"],
        help="The evaluator to use (gemini or gpt)",
    )
    parser.add_argument("--dataset", help="The dataset (database) to process")
    parser.add_argument("--tag", help="Optional tag to add to the results document")
    args = parser.parse_args()

    tag = None

    if args.tag:
        tag = args.tag

    model = args.model
    evaluator = "gem" if args.evaluator.lower() == "gemini" else args.evaluator.lower()
    dataset = args.dataset

    client = get_client()
    db = client[dataset]

    llm_or_f1_total_yes = 0
    llm_or_f1_total_no = 0

    llm_total_yes = 0
    llm_total_no = 0
    collection_results = {}

    reasonings = [
        "cot",
        "evidence",
        "decomposition",
        "faithful",
        "pot",
        "meta",
        "meta_3_step",
        "clean_meta_3_step",
        "not",
        "tot",
        "got",
        "scp",
        "clear"
    ]

    for collection_name in db.list_collection_names():
        if collection_name in reasonings:  # Skip the results collection
            print(collection_name)
            collection = db[collection_name]
            llm_or_f1_results, llm_results, f1_score = process_collection(
                collection, model, evaluator, dataset
            )

            # print(llm_or_f1_results)
            llm_or_f1_yes_count, llm_or_f1_no_count = llm_or_f1_results
            llm_yes_count, llm_no_count = llm_results

            llm_or_f1_total_yes += llm_or_f1_yes_count
            llm_or_f1_total_no += llm_or_f1_no_count

            llm_total_yes += llm_yes_count
            llm_total_no += llm_no_count

            collection_results[collection_name] = {
                "llm_yes": llm_yes_count,
                "llm_no": llm_no_count,
                "llm_total": llm_yes_count + llm_no_count,
                "Accuracy_LLM": (llm_yes_count / TOTAL_COUNTS[dataset]),
                "llm_or_f1_yes": llm_or_f1_yes_count,
                "llm_or_f1_no": llm_or_f1_no_count,
                "llm_or_f1_total": llm_or_f1_yes_count + llm_or_f1_no_count,
                "Accuracy_LLM_OR_F1": (llm_or_f1_yes_count / TOTAL_COUNTS[dataset]),
                "Total_QA_pairs": TOTAL_COUNTS[dataset],
                "f1_score": f1_score,
            }
    print("####Collection Results")
    print(collection_results)

    # Prepare the results document
    results_doc = {
        "model": model,
        "evaluator": args.evaluator,
        "tag": tag,
        "timestamp": datetime.utcnow(),
        "collection_results": collection_results,
        "total_results": {
            "LLM_Total_Yes": llm_total_yes,
            "LLM_Total_No": llm_total_no,
            "LLM_Total_Evaluated": llm_total_yes + llm_total_no,
            "LLM_OR_F1_Total_Yes": llm_or_f1_total_yes,
            "LLM_OR_F1_Total_No": llm_or_f1_total_no,
            "LLM_OR_F1_Total_Evaluated": llm_or_f1_total_yes + llm_or_f1_total_no,
        },
    }

    # Insert the results document into the results collection
    results_collection = db["results"]
    result = results_collection.insert_one(results_doc)

    print(f"Summary for model: {model}")
    print(f"Evaluator: {args.evaluator}")
    print("\nResults per collection:")
    # for collection_name, counts in collection_results.items():
    #     print(f"{collection_name}: Yes: {counts['Yes']}, No: {counts['No']}")
    print(f"\nTotal results across all collections:")
    print(
        {
            "LLM_Total_Yes": llm_total_yes,
            "LLM_Total_No": llm_total_no,
            "LLM_Total_Evaluated": llm_total_yes + llm_total_no,
            "LLM_OR_F1_Total_Yes": llm_or_f1_total_yes,
            "LLM_OR_F1_Total_No": llm_or_f1_total_no,
            "LLM_OR_F1_Total_Evaluated": llm_or_f1_total_yes + llm_or_f1_total_no,
        }
    )
    print(f"\nResults document inserted with ID: {result.inserted_id}")


if __name__ == "__main__":
    main()
