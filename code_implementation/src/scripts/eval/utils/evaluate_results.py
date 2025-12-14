import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm
import time
import re
import math
from rouge_score import rouge_scorer
from nltk.translate import meteor_score
import evaluate
import glob
import ast


def get_f1_score(prediction, reference):

    prediction = str(prediction)
    reference = str(reference)

    # Load the SQuAD v2 metric
    metric = evaluate.load("squad_v2")

    # Prepare data in the required format
    predictions = [
        {"id": "1", "prediction_text": prediction, "no_answer_probability": 0.0}
    ]
    references = [{"id": "1", "answers": {"text": [reference], "answer_start": [0]}}]

    # Compute the F1 score and other metrics
    results = metric.compute(predictions=predictions, references=references)

    # Extract the F1 score
    f1_score = results["f1"]
    return f1_score


def categorical_to_numeric(text):
    categorical_to_numeric = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    for key, value in zip(
        categorical_to_numeric.keys(), categorical_to_numeric.values()
    ):
        text = re.sub(str(key), str(value), text)

    return text


def analyse_answer(gold_answer, predicted_answer):
    corrected_answer = ""
    corrected_gold_answer = ""

    answer = str(gold_answer)
    answer = answer.lower()
    answer = answer.strip()
    if answer.startswith("'") and answer.endswith("'"):
        answer = answer[1:-1]
    answer = answer.strip()
    answer = answer.replace("\n", "")
    answer = answer.replace("–", "-")
    answer = answer.replace('"', "")
    answer = answer.replace("~", "")
    answer = answer.replace("#", "")
    answer = answer.replace("%", "")
    answer = answer.replace(">", "")
    answer = answer.replace("+", "")
    answer = answer.replace("°c", "")
    answer = answer.replace("hours", "")
    answer = answer.replace("mm", "")
    answer = answer.replace("days", "")
    answer = answer.replace("us$", "")
    answer = answer.replace("usd$", "")
    answer = answer.replace("$", "")
    answer = answer.replace("€", "")
    answer = answer.replace(" °c", "°c")
    answer = answer.replace("%", "")
    answer = re.sub(r"\.$", "", answer)
    answer = re.sub(r"^\.", "", answer)
    answer = categorical_to_numeric(answer)
    answer = re.sub(r" (\()(.*)(\))$", r"", answer)
    answer = re.sub(r"(\d)(rd|th|st|nd)", r"\1", answer)
    answer = re.sub(r"(\d{2})(\d{2})-(\d{2})$", r"\1\2-\1\3", answer)

    answer = re.sub(
        r"^(almost |over |after |in or before |at age |in the year |at the age of |age |age of |he was )?(\d+)( active)? (gold |bronze |silver )?(million|goal|vehicle|win|race|episode|single|langley|album|team|hurricane|time|year|month|day|week|month|season|medal|minute|hour|second)(s)?(( ago)|( old)|( longer)|( almost)|( after))?(.)?$",
        r"\2",
        answer,
    )
    answer = re.sub(
        r"^(at least|at the age of |after the age of |nearly |age of )(\d+)$",
        r"\2",
        answer,
    )
    answer = re.sub(r"^(bronze|gold|silver) (medal)$ ", r"\2", answer)
    answer = re.sub(r"(\d+) (million|billion)", r"\1", answer)

    try:
        parsed = ast.literal_eval(answer)
        if isinstance(parsed, list) and len(parsed) == 1:
            answer = str(parsed[0])
    except Exception as e:
        # print(f"Exception occured {e}")
        pass

    corrected_gold_answer = answer

    answer = predicted_answer
    answer = answer.lower()
    answer = answer.strip()
    answer = answer.replace("final answer:", "").strip()
    answer = answer.replace("final answer :", "").strip()
    if answer.startswith("'") and answer.endswith("'"):
        answer = answer[1:-1]
    answer = answer.strip()
    answer = answer.replace("\n", "")
    answer = answer.replace("–", "-")
    answer = answer.replace('"', "")
    answer = answer.replace("~", "")
    answer = answer.replace("#", "")
    answer = answer.replace("%", "")
    answer = answer.replace(">", "")
    answer = answer.replace("+", "")
    answer = answer.replace("°c", "")
    answer = answer.replace("hours", "")
    answer = answer.replace("mm", "")
    answer = answer.replace("days", "")
    answer = answer.replace("us$", "")
    answer = answer.replace("usd$", "")
    answer = answer.replace("€", "")
    answer = answer.replace("$", "")
    answer = answer.replace("%", "")
    answer = re.sub(r"\.$", "", answer)
    answer = re.sub(r"^\.", "", answer)
    answer = categorical_to_numeric(answer)
    answer = re.sub(r"(\d)(rd|th|st|nd)", r"\1", answer)
    answer = re.sub(r"(\d{2})(\d{2})-(\d{2})$", r"\1\2-\1\3", answer)

    answer = re.sub(
        r"^(over |after |in or before |at age |percentage points |in the year |at the age of |age |age of |he was )?(\d+)( active)? (gold |bronze |silver )?(million|goal|vehicle|win|race|episode|single|langley|album|team|hurricane|time|year|month|day|week|month|season|medal|minute|hour|second)(s)?(( ago)|( old)|( longer)|( almost)|( after))?(.)?$",
        r"\2",
        answer,
    )
    answer = re.sub(r"^(bronze|gold|silver) (medal)$ ", r"\2", answer)
    answer = re.sub(r"(\d+) (million|billion)", r"\1", answer)

    if " " + corrected_gold_answer + " " in answer:
        answer = corrected_gold_answer

    if " " + corrected_gold_answer + "," in answer:
        answer = corrected_gold_answer

    if " " + corrected_gold_answer + ". " in answer:
        answer = corrected_gold_answer

    if corrected_gold_answer in answer:
        answer = corrected_gold_answer

    for w in [" ", ",", "-year", "-minute"]:
        if answer.startswith(corrected_gold_answer + w):
            answer = corrected_gold_answer

    if answer.endswith(" " + corrected_gold_answer):
        answer = corrected_gold_answer

    if answer != corrected_gold_answer:
        if corrected_gold_answer in answer:
            alter_answer = re.sub(r".*(\()(.*)(\))$", r"\2", answer)
            if alter_answer != answer:
                if alter_answer == corrected_gold_answer:
                    answer = corrected_gold_answer

    try:
        parsed = ast.literal_eval(answer)
        if isinstance(parsed, list) and len(parsed) == 1:
            answer = str(parsed[0])
    except Exception as e:
        # print(f"Exception occured {e}")
        pass

    corrected_answer = answer

    # print(f"After everything CA: {corrected_answer}   CGA : {corrected_gold_answer}")

    try:
        if not re.match(r"^\d{4}$", corrected_gold_answer):

            # print("inside digit match")
            if corrected_gold_answer[-1] == "%":
                corrected_gold_answer = corrected_gold_answer[:-1].strip()
                corrected_gold_answer = float(corrected_gold_answer) / 100
            else:
                corrected_gold_answer = float(corrected_gold_answer.replace(",", ""))

            if corrected_answer[-1] == "%":
                corrected_answer = corrected_answer[:-1].strip()
                corrected_answer = float(corrected_answer) / 100
            else:
                corrected_answer = float(corrected_answer.replace(",", ""))

            # print(f'After to number CA: {corrected_answer}   CGA : {corrected_gold_answer}')

            x = math.isclose(
                corrected_gold_answer, corrected_answer, rel_tol=0.01, abs_tol=0.001
            )
            y = math.isclose(
                corrected_gold_answer * 100,
                corrected_answer,
                rel_tol=0.01,
                abs_tol=0.001,
            )
            z = math.isclose(
                corrected_gold_answer,
                corrected_answer * 100,
                rel_tol=0.01,
                abs_tol=0.001,
            )

            if (x | y | z) == 1:
                if corrected_answer != corrected_gold_answer:
                    corrected_answer = corrected_gold_answer
                    # print(predicted_answer, gold_answer)

    except Exception as e:
        # print(f"Exception occured {e}")
        pass

    return {
        "corrected_answer": corrected_answer,
        "corrected_gold_answer": corrected_gold_answer,
        "answer": predicted_answer,
        "gold_answer": gold_answer,
    }


def get_rouge_scores(predicted_answer, actual_answer):
    actual_answer = str(actual_answer)
    predicted_answer = str(predicted_answer)
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    scores = scorer.score(predicted_answer, actual_answer)
    return scores


def get_rouge(df, c1, c2):
    r1 = 0
    rl = 0
    for i in df.index:
        r1 += get_rouge_scores(df[c2][i], df[c1][i])["rouge1"][2]
        rl += get_rouge_scores(df[c2][i], df[c1][i])["rougeL"][2]
    return r1 / len(df), rl / len(df)


def calculate_meteor_score(reference, candidate):
    # Tokenize the reference and candidate sentences
    reference_tokens = reference.split()
    candidate_tokens = candidate.split()

    # Calculate the METEOR score
    score = meteor_score.meteor_score([reference_tokens], candidate_tokens)

    # Return the METEOR score
    return score


# Example usage
def get_meteor(df, c1, c2):
    meteor_score = 0
    for i in df.index:
        meteor_score += calculate_meteor_score(str(df[c1][i]), str(df[c2][i]))
    meteor_score /= len(df)
    return meteor_score


def get_squad_v2_metric(df_or_actual, c1_or_pred=None, c2=None):
    """
    Calculate SQuAD v2 metrics for question answering.
    
    Can be called in two ways:
    1. get_squad_v2_metric(df, 'actual_column', 'pred_column') - with DataFrame and column names
    2. get_squad_v2_metric(actual_list, pred_list) - with direct lists
    
    Returns evaluation metrics, individual F1 scores, and individual exact match scores.
    """
    predictions = []
    references = []
    squad_v2_metric = evaluate.load("squad_v2")
    f1_score = []
    exact_match_score = []

    # Check which calling pattern is being used
    if c2 is None:
        # We're being called with actual_list, pred_list
        actuals = df_or_actual
        predicteds = c1_or_pred
        
        for i, (actual, predicted) in enumerate(zip(actuals, predicteds)):
            predictions.append({
                "id": str(i),
                "prediction_text": str(predicted),
                "no_answer_probability": 0.0
            })
            
            references.append({
                "id": str(i),
                "answers": {
                    "text": [str(actual)],
                    "answer_start": [0]
                }
            })
            
            # Calculate individual scores
            ind_score = squad_v2_metric.compute(
                predictions=[predictions[-1]],
                references=[references[-1]]
            )
            
            f1_score.append(ind_score["f1"])
            exact_match_score.append(ind_score["exact"])
    else:
        # Original behavior with DataFrame and column names
        for i, (actual, predicted) in enumerate(zip(df_or_actual[c1_or_pred], df_or_actual[c2])):
            predictions.append({
                "id": str(i),
                "prediction_text": str(predicted),
                "no_answer_probability": 0.0
            })
            
            references.append({
                "id": str(i),
                "answers": {
                    "text": [str(actual)],
                    "answer_start": [0]
                }
            })
            
            # Calculate individual scores
            ind_score = squad_v2_metric.compute(
                predictions=[predictions[-1]],
                references=[references[-1]]
            )
            
            f1_score.append(ind_score["f1"])
            exact_match_score.append(ind_score["exact"])

    # Calculate overall score
    result = squad_v2_metric.compute(
        predictions=predictions, 
        references=references
    )
    
    return result, f1_score, exact_match_score


def analyse_results(df, path):

    actual = []
    pred = []

    for i in df.index:
        result = analyse_answer(str(df["answer"][i]), str(df["output"][i]))
        # a,p = analyse_answer(df_res['actual_answer'][i], df_res['predicted_answer'][i])
        # print(result)
        gold_answers = result["corrected_gold_answer"]
        pred_answers = result["corrected_answer"]
        actual.append(str(gold_answers))
        pred.append(str(pred_answers))

    df["conv_actual_answer"] = actual
    df["conv_predicted_answer"] = pred

    squad, ind_f1, ind_exact = get_squad_v2_metric(
        df, "conv_actual_answer", "conv_predicted_answer"
    )
    rouge = get_rouge(df, "conv_actual_answer", "conv_predicted_answer")
    met = get_meteor(df, "conv_actual_answer", "conv_predicted_answer")

    df["f1_score"] = ind_f1
    df["exact"] = ind_exact
    # Category Zeroshot
    # print(df['SportCategory'].iloc[0] + ":")
    # Splitwise fewshot
    print("exact match score: ", squad["exact"])
    print("f1 score: ", squad["f1"])
    print("rouge score: ", rouge)
    print("meteor score: ", met)

    df.to_csv(path, index=False)
    print(f"File after evaluation saved successfully at : {path}")


def get_max_f1(df):
    # Creating 'conv_actual_answer' and 'conv_predicted_answer' based on the condition
    df["conv_actual_answer"] = df.apply(
        lambda row: (
            row["extract_conv_actual_answer"]
            if row["f1_extract"] >= row["f1_code"]
            else row["code_conv_actual_answer"]
        ),
        axis=1,
    )
    df["conv_predicted_answer"] = df.apply(
        lambda row: (
            row["extract_conv_predicted_answer"]
            if row["f1_extract"] >= row["f1_code"]
            else row["code_conv_predicted_answer"]
        ),
        axis=1,
    )

    # Dropping the original 4 columns
    df = df.drop(
        [
            "extract_conv_actual_answer",
            "extract_conv_predicted_answer",
            "code_conv_actual_answer",
            "code_conv_predicted_answer",
            "f1_extract",
            "f1_code",
        ],
        axis=1,
    )

    return df


def analyse_dynamic(df, path):
    actual_extract = []
    pred_extract = []

    for i in df.index:
        result = analyse_answer(str(df["answer"][i]), str(df["output"][i]))
        # a,p = analyse_answer(df_res['actual_answer'][i], df_res['predicted_answer'][i])
        # print(result)
        gold_answers = result["corrected_gold_answer"]
        pred_answers = result["corrected_answer"]
        actual_extract.append(str(gold_answers))
        pred_extract.append(str(pred_answers))

    df["extract_conv_actual_answer"] = actual_extract
    df["extract_conv_predicted_answer"] = pred_extract

    squad_extract, ind_f1_extract, ind_exact_extract = get_squad_v2_metric(
        df, "extract_conv_actual_answer", "extract_conv_predicted_answer"
    )

    actual_code = []
    pred_code = []

    for i in df.index:
        result = analyse_answer(str(df["answer"][i]), str(df["code_output"][i]))
        # a,p = analyse_answer(df_res['actual_answer'][i], df_res['predicted_answer'][i])
        # print(result)
        gold_answers = result["corrected_gold_answer"]
        pred_answers = result["corrected_answer"]
        actual_code.append(str(gold_answers))
        pred_code.append(str(pred_answers))

    df["code_conv_actual_answer"] = actual_code
    df["code_conv_predicted_answer"] = pred_code

    squad_code, ind_f1_code, ind_exact_code = get_squad_v2_metric(
        df, "code_conv_actual_answer", "code_conv_predicted_answer"
    )

    df["f1_extract"] = ind_f1_extract
    df["f1_code"] = ind_f1_code
    df = get_max_f1(df)

    squad, ind_f1, ind_exact = get_squad_v2_metric(
        df, "conv_actual_answer", "conv_predicted_answer"
    )
    rouge = get_rouge(df, "conv_actual_answer", "conv_predicted_answer")
    met = get_meteor(df, "conv_actual_answer", "conv_predicted_answer")

    df["f1_score"] = ind_f1
    df["exact"] = ind_exact
    # Category Zeroshot
    # print(df['SportCategory'].iloc[0] + ":")
    # Splitwise fewshot
    print("exact match score: ", squad["exact"])
    print("f1 score: ", squad["f1"])
    print("rouge score: ", rouge)
    print("meteor score: ", met)

    df.to_csv(path, index=False)
    print(f"File after evaluation saved successfully at : {path}")
