import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm
import time
import re
import math
from rouge_score import rouge_scorer
import nltk
from nltk.translate import meteor_score
import evaluate
import glob
from datasets import load_metric

nltk.download("wordnet")


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
    # answer = answer.replace("%","")
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
    # answer = answer.replace("%","")
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
    answer = re.sub(r"\.$", "", answer)
    answer = re.sub(r"^\.", "", answer)
    answer = categorical_to_numeric(answer)
    answer = re.sub(r"(\d)(rd|th|st|nd)", r"\1", answer)
    answer = re.sub(r"(\d{2})(\d{2})-(\d{2})$", r"\1\2-\1\3", answer)

    answer = re.sub(
        r"^(over |after |in or before |at age |in the year |at the age of |age |age of |he was )?(\d+)( active)? (gold |bronze |silver )?(million|goal|vehicle|win|race|episode|single|langley|album|team|hurricane|time|year|month|day|week|month|season|medal|minute|hour|second)(s)?(( ago)|( old)|( longer)|( almost)|( after))?(.)?$",
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

    corrected_answer = answer

    try:
        if not re.match(r"^\d{4}$", corrected_gold_answer):

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

    except:
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


def get_squad_v2_metric(df, c1, c2):
    predictions = []
    references = []
    squad_v2_metric = load_metric("squad_v2")
    f1_score = []
    exact_match_score = []

    for i, (actual, predicted) in enumerate(zip(df[c1], df[c2])):
        predictions.append(
            {
                "id": str(i),
                "prediction_text": str(predicted),
                "no_answer_probability": 0.0,  # Assuming no answer probability is always 0
            }
        )

        references.append(
            {
                "id": str(i),
                "answers": [
                    {"text": str(actual), "answer_start": 0}
                ],  # Assuming answer always starts at position 0
            }
        )

        ind_score = squad_v2_metric.compute(
            predictions=[
                {
                    "id": str(i),
                    "prediction_text": str(predicted),
                    "no_answer_probability": 0.0,  # Assuming no answer probability is always 0
                }
            ],
            references=[
                {
                    "id": str(i),
                    "answers": [
                        {"text": str(actual), "answer_start": 0}
                    ],  # Assuming answer always starts at position 0
                }
            ],
        )

        f1_score.append(ind_score["f1"])
        exact_match_score.append(ind_score["exact"])

    # Call the squad_v2_metric.compute function with the formatted data
    results = squad_v2_metric.compute(predictions=predictions, references=references)
    return results, f1_score, exact_match_score


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

    df.to_csv(path)
    print(f"File after evaluation saved successfully at : {path}")


def analyse_results_meta(df, path):

    actual = []
    pred = []

    for i in df.index:
        # Check if 'output' column is not NaN or None, otherwise use 'answer_extraction' column
        if pd.notna(df["output"][i]) and df["output"][i] != "NONE":
            answer_to_evaluate = str(df["output"][i])
        else:
            answer_to_evaluate = str(df["answer_extraction"][i])
        result = analyse_answer(str(df["answer"][i]), answer_to_evaluate)

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

    df.to_csv(path)
    print(f"File after evaluation saved successfully at : {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", default="", type=str, help="Input file Path")

    args = parser.parse_args()
    INPUT_PATH = args.input_path

    csv_files = glob.glob(os.path.join(INPUT_PATH, "*.csv"))

    print(f"Running Evaluation for : {INPUT_PATH}")

    file_read_count = 0
    # Iterate through the list of CSV files
    for file in csv_files:

        # Read the CSV file into a DataFrame
        data = pd.read_csv(file)

        # Print the name of the file
        print(f"Evaluation for : {os.path.basename(file)}:")

        if "meta".lower() in os.path.basename(file).lower():
            print("Meta")
            analyse_results_meta(data, str(file))
            # Do this later
            continue

        else:
            print("Normal Analysis")
            analyse_results(data, str(file))

        print("\n" + "=" * 50 + "\n")
