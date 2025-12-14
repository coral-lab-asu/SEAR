import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import UpdateOne
from dotenv import load_dotenv
import utils
import utils.evaluate_results
import utils.utils
import evaluate


def create_list(documents, key):
    """
    Extract values from a list of documents for a given key.

    :param documents: List of documents (dictionaries)
    :param key: Key to extract values for
    :return: List of values for the given key
    """
    return [doc.get(key) for doc in documents]


def get_prompt_extraction(question, answer):
    return f"""You are given with a question and answer. Your task is to respond by extracting the final answer from the overall answer.
Instructions:
1. Provide the answer in a straigtforward manner and keep it within 1 to 10 words.
2. Respond only with the information provided. Do not use external knowledge in your response.
3. If there are multiple answers, Response should be a list of all answers.
4. If a conclusive answer cannot be determined, respond with "Not enough information provided."

Few Examples of question and answers are given with Response for reference:

Example 1:
Question: which game did the opponent score only 7 points ?
Answer: 
Subquestions:
1. What is the column containing the opponent names and their corresponding scores?
2. Which game had the opponent score only 7 points?

Let's answer each subquestion:

Subquestion 1:
What is the column containing the opponent names and their corresponding scores?
Answer:
- The opponent names are in the "c3_raw" column.
- The opponent scores are in the "c7_number2" column.

Subquestion 2:
Which game had the opponent score only 7 points?
Answer:
- The opponent score of 7 points corresponds to the 11th game (index 10).
- Checking the corresponding opponent in the "c3_raw" column, it was "san diego state".

Final Answer: San Diego State

Response: San Diego State

Example 2:
Question: how many total seasons are given in the chart ?
Answer:
Subquestion 1: How many unique season entries are present in the table? (Independent)

Subquestion 2: Do all the season entries represent unique seasons, or are there any repeated seasons? (Dependent on sq1)

Subquestion 3: If there are repeated seasons, how many distinct seasons are there excluding any duplicates? (Dependent on sq2)
Let's answer each subquestion:

Subquestion 1: How many unique season entries are present in the table? (Independent)
Answer: 
- The season data is present in the column labeled "c1".
- Count the number of unique entries in the "c1" column.

Subquestion 2: Do all the season entries represent unique seasons, or are there any repeated seasons? (Dependent on sq1)
Answer:
- Check if all season entries are unique or if there are any duplicates present.

Subquestion 3: If there are repeated seasons, how many distinct seasons are there excluding any duplicates? (Dependent on sq2)
Answer:
- If there are repeated seasons, count the total number of distinct seasons after removing duplicates.

Final Answer: {{Answer}}

Your final answer will consider the number of distinct seasons present in the table without any repetitions.

Response: Not enough information provided.

Example 3:
Question: how many games did they win in 2009 ?
Answer: 
### Extracted Evidence:
1. **`c2_year`**: Contains the year of the game.
   - `c2_year`: [2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009]
   
2. **`c5_result`**: Contains the result of each game.
   - `c5_result`: ["w", "l", "l", "w", "w", "w", "l", "l", "w", "l", "w", "l", "l", "l", "l", "w"]

### Final Answer:
The number of games won in 2009 can be found by counting the number of "w" (win) entries in the `c5_result` column for the year 2009.

**Final Answer: 6 games were won in 2009.**

Response: 6

Example 4:
Question: how many times was the mean value of resps among families at the top higher than those at the bottom of the distribution in 1999?
Answer: 
Given the table detailing registered education savings plan holdings of economic families with children across different categories and years, we are tasked with determining the difference in the mean value of RESP holdings between families at the top and bottom of the distribution in 1999.

From the data provided in the table for the year 1999:

- For families at the bottom of the income quintile:
  - Mean value of RESP: $746

- For families at the top of the income quintile:
  - Mean value of RESP: $3,134

To find the difference in mean value of RESP holdings between the top and bottom income quintiles in 1999:
$3,134 / $746 = approximately 4.2 times

Thus, the mean value of RESP holdings among families at the top was approximately 4.2 times higher than those at the bottom of the distribution in 1999.

Final Answer: 4.2 times

Response: 4.2

Example 5:
Question: which league did towers play for brentford in 1958-59?
Answer: 
Based on the provided table, the relevant rows and columns for the question are as follows:

| Club      | Season | League           | Apps | Goals | FA Cup | League Cup | Total  |
|------------|--------|------------------|------|-------|--------|------------|--------|
| Brentford | 1958-59 | Third Division   | 46   | 32    | 4      | 5          | 50     |

Final Answer: Towers played for Brentford in the Third Division in 1958-59.

Response: Third Division

Example 6:
Question: In which years was the selected financial data provided?
Answer:
Subquestion 1: What is the year for the selected financial data provided for Net sales?
Answer: The selected financial data for Net Sales was provided for the years 2015 to 2019.

Subquestion 2: What is the year for the selected financial data provided for Gross profit?
Answer: The selected financial data for Gross Profit was provided for the years 2015 to 2019.

Subquestion 3: What is the year for the selected financial data provided for Net income from continuing operations?
Answer: The selected financial data for Net Income from Continuing Operations was provided for the years 2015 to 2019.

Subquestion 4: What is the year for the selected financial data provided for Total assets?
Answer: The selected financial data for Total Assets was provided for the years 2015 to 2019.

Subquestion 5: What is the year for the selected financial data provided for Long-term obligations?
Answer: The selected financial data for Long-term Obligations was provided for the years 2015 to 2019.

Subquestion 6: What is the year for the selected financial data provided for Other long-term liabilities?
Answer: The selected financial data for Other Long-term Liabilities was provided for the years 2015 to 2019.

Subquestion 7: What is the year for the selected financial data provided for Stockholders' equity?
Answer: The selected financial data for Stockholders' Equity was provided for the years 2015 to 2019.

Final Answer : The selected financial data was provided for the years 2015 to 2019.

Response: ['2015', '2016', '2017', '2018', '2019']

Example 7:
Question: What is the high sale and low sale of the first quarter of 2019 respectively? 
Answer:
Subquestion 1: What is the high sale price in the first quarter of 2019?
Answer: From the table, the high sale price in the first quarter of 2019 is $8.95.

Subquestion 2: What is the low sale price in the first quarter of 2019?
Answer: From the table, the low sale price in the first quarter of 2019 is $7.30.

Final Answer: High Sale Price: $8.95, Low Sale Price: $7.30

Response: ['$8.95','$7.30']

For the following question and answer provide your response:

Question: {question}
Answer:
{answer}

Response:"""


def get_code_output(dataset, model, reasoning):
    client = utils.utils.get_client()
    db = client[dataset]
    print(f"Debug: Reasoning {reasoning}")
    collection = db[reasoning]

    query = {"model": model}
    documents = list(collection.find(query))
    code_outputs = []

    for ind, doc in tqdm(
        enumerate(documents), total=len(documents), desc="Processing code documents"
    ):
        out = ""
        response = doc.get("response", "")
        if response is not None:
            code = utils.utils.extract_code(response)
            # print("helllo")
            try:
                out = utils.utils.get_code_output(code)
            except Exception as e:
                out = f"Error: {str(e)}"
        code_outputs.append(out)

    # Update documents with extracted responses
    update_operations = []
    print("Appending code outputs")
    for ind, result in enumerate(code_outputs):
        update_operations.append(
            UpdateOne(
                {"_id": documents[ind]["_id"]},
                {"$set": {"code_output": result}},
                upsert=True,
            )
        )

    if update_operations:
        collection.bulk_write(update_operations)
        print(f"Updated {len(update_operations)} documents with extracted responses.")

    client.close()


def process_reasoning_data(dataset, model, reasoning):
    client = utils.utils.get_client()
    db = client[dataset]
    collection = db[reasoning]

    query = {"model": model}
    documents = list(collection.find(query))

    outputs = [None] * len(documents)

    gemini_model = utils.utils.get_gemini_model()

    def process_document(ind, document):
        question = document.get("question", "")
        text_response = document.get("response", "")
        input_prompt = get_prompt_extraction(question, text_response)
        itr = 0
        while True:
            try:
                if itr == 3:
                    result_gemini = "res"
                else:
                    result_gemini = utils.utils.gemini_response(
                        input_prompt, gemini_model
                    )
                break
            except Exception as e:
                itr += 1
                print(f"Error for index {ind}: {e}")
                if itr == 3:
                    result_gemini = "res"
                    break
                time.sleep(5)
        return ind, result_gemini

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_document, ind, doc): ind
            for ind, doc in enumerate(documents)
        }
        for future in tqdm(as_completed(futures), total=len(futures)):
            ind, result = future.result()
            outputs[ind] = result

    # Update documents with extracted responses
    update_operations = []
    for ind, result in enumerate(outputs):
        update_operations.append(
            UpdateOne(
                {"_id": documents[ind]["_id"]},
                {"$set": {"extracted_response": result, "evaluated": False}},
                upsert=True,
            )
        )

    if update_operations:
        collection.bulk_write(update_operations)
        print(f"Updated {len(update_operations)} documents with extracted responses.")

    client.close()


def get_f1_scores(dataset, model, reasoning):
    client = utils.utils.get_client()
    db = client[dataset]
    print(f"Debug: Reasoning {reasoning}, model {model}")
    collection = db[reasoning]

    query = {"model": model}

    try:
        # Try to get documents with better error handling
        documents = list(collection.find(query))
        if not documents:
            print(f"Warning: No documents found for {model} in {reasoning}")
            client.close()
            return
            
        print(f"Total Documents for F1 score : {len(documents)}")

        extracted_answers = create_list(documents, "extracted_response")
        code_answers = create_list(documents, "code_output")
        gold_answers = create_list(documents, "answer")

        conv_gold_text = []
        conv_gold_code = []
        conv_pred = []
        conv_code = []

        for extracted_answer, code_answer, gold_answer in zip(
            extracted_answers, code_answers, gold_answers
        ):
            result_text = utils.evaluate_results.analyse_answer(
                str(gold_answer), str(extracted_answer)
            )
            result_code = utils.evaluate_results.analyse_answer(
                str(gold_answer), str(code_answer)
            )
            
            conv_gold_text.append(result_text["corrected_gold_answer"])
            conv_pred.append(result_text["corrected_answer"])
            conv_gold_code.append(result_code["corrected_gold_answer"])
            conv_code.append(result_code["corrected_answer"])

        # Initialize variables for metrics
        squad_text = {"exact": 0, "f1": 0}
        squad_code = {"exact": 0, "f1": 0}
        f1_scores_text = [0] * len(conv_gold_text)
        f1_scores_code = [0] * len(conv_gold_code)
        exact_match_text = [0] * len(conv_gold_text)
        exact_match_code = [0] * len(conv_gold_code)
        
        # Try SQuAD metrics first for text responses
        try:
            print("Attempting SQuAD metric calculation for text responses...")
            with utils.utils.time_limit(120):  # Increased timeout to 120 seconds
                squad_text, f1_scores_text, exact_match_text = (
                    utils.evaluate_results.get_squad_v2_metric(conv_gold_text, conv_pred)
                )
            print("Successfully calculated SQuAD metrics for text responses")
        except Exception as e:
            print(f"SQuAD calculation failed for text, using fallback: {e}")
            # Manual calculation as fallback
            print("Using manual F1 score calculation for text responses...")
            f1_scores_text = [utils.evaluate_results.calculate_f1(gold, pred) 
                              for gold, pred in zip(conv_gold_text, conv_pred)]
            exact_match_text = [1.0 if gold == pred else 0.0 
                               for gold, pred in zip(conv_gold_text, conv_pred)]
            # Calculate aggregate metrics
            if f1_scores_text:
                squad_text["f1"] = sum(f1_scores_text) / len(f1_scores_text)
            if exact_match_text:
                squad_text["exact"] = sum(exact_match_text) / len(exact_match_text)

        # Try SQuAD metrics for code outputs
        try:
            print("Attempting SQuAD metric calculation for code outputs...")
            with utils.utils.time_limit(120):  # Increased timeout to 120 seconds
                squad_code, f1_scores_code, exact_match_code = (
                    utils.evaluate_results.get_squad_v2_metric(conv_gold_code, conv_code)
                )
            print("Successfully calculated SQuAD metrics for code outputs")
        except Exception as e:
            print(f"SQuAD calculation failed for code, using fallback: {e}")
            # Manual calculation as fallback
            print("Using manual F1 score calculation for code outputs...")
            f1_scores_code = [utils.evaluate_results.calculate_f1(gold, pred) 
                              for gold, pred in zip(conv_gold_code, conv_code)]
            exact_match_code = [1.0 if gold == pred else 0.0 
                               for gold, pred in zip(conv_gold_code, conv_code)]
            # Calculate aggregate metrics
            if f1_scores_code:
                squad_code["f1"] = sum(f1_scores_code) / len(f1_scores_code)
            if exact_match_code:
                squad_code["exact"] = sum(exact_match_code) / len(exact_match_code)

        # Calculate final F1 scores (max of text and code)
        f1_final = []
        for ind in range(len(f1_scores_text)):
            text_score = f1_scores_text[ind]
            code_score = f1_scores_code[ind]
            
            # Compare the numeric values
            f1_final.append(max(text_score, code_score))

        # Update MongoDB with F1 scores
        update_operations = []
        for ind, f1_fin in enumerate(f1_final):
            update_operations.append(
                UpdateOne(
                    {"_id": documents[ind]["_id"]},
                    {
                        "$set": {
                            "f1_score_extracted_response": f1_scores_text[ind],
                            "f1_score_code_output": f1_scores_code[ind],
                            "f1_final": f1_fin,
                            "evaluated": False,
                            "gem_eval_extracted_response": None,
                            "gem_eval_code_output": None,
                            "gpt_eval_extracted_response": None,
                            "gpt_eval_code_output": None,
                        }
                    },
                    upsert=True,
                )
            )

        if update_operations:
            collection.bulk_write(update_operations)
            print(f"Updated {len(update_operations)} documents with F1 scores.")

        # Print F1 score summary
        print("###############################################################")
        print(f"F1 Score for {dataset} : {reasoning} : {model}  (Text)")
        print("exact match score: ", squad_text["exact"])
        print("f1 score: ", squad_text["f1"])

        print("")
        print(f"F1 Score for {dataset} : {reasoning} : {model}  (Code)")
        print("exact match score: ", squad_code["exact"])
        print("f1 score: ", squad_code["f1"])
        print("###############################################################")
        
    except Exception as e:
        print(f"An unexpected error occurred in get_f1_scores: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Always close the MongoDB connection
        client.close()
def main(dataset, model, reasoning):

    print(
        f"Running Answer Extraction for Dataset: {dataset}, Model: {model}, Reasoning: {reasoning}"
    )

    reasoning_types = [
        "cot",
        "decomposition",
        "evidence",
        "meta",
        "meta_3_step",
        "clean_meta_3_step",
        "not",
        "tot",
        "got",
        "scp",
        "clear"
    ]
    reasoning_types_code = [
        "pot",
        "faithful",
        "meta",
        "meta_3_step",
        "clean_meta_3_step",
        "not",
        "tot",
        "got",
        "scp",
        "clear"

    ]

    if "all" in reasoning:
        reasoning = list(set(reasoning_types + reasoning_types_code))

    for reason in reasoning:

        if (reason not in reasoning_types) and (reason not in reasoning_types_code):
            print("Error: Invalid Reasoning Type")
            return

        if reason in reasoning_types:
            print(f"Processing reasoning type (Answer Extraction): {reason}")
            process_reasoning_data(dataset, model, reason)

        if reason in reasoning_types_code:
            print(f"Processing reasoning type (Code Output): {reason}")
            get_code_output(dataset, model, reason)

        get_f1_scores(dataset, model, reason)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=str, help="Dataset name")
    parser.add_argument("--model", required=True, type=str, help="Model name")
    parser.add_argument("--reasoning", required=True, nargs="+", help="Reasoning types")

    args = parser.parse_args()

    main(dataset=args.dataset, model=args.model, reasoning=args.reasoning)
