import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import re

from datetime import datetime
from dateutil import parser

import logging

from urllib.error import HTTPError

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_mongodb_client():

    load_dotenv()
    uri = os.getenv('MONGODB_URI')

    return MongoClient(uri, server_api=ServerApi('1'))

def get_gpt_results(collection):

    try:
        matching_docs = list(collection.find({
            'model': {'$regex': 'gpt', '$not': {'$regex': 'gpt4omini-finetune'}},
            'timestamp': {'$exists': True},
            'collection_results': {'$exists': True}
        }))

        sorted_docs = sorted(matching_docs, key=lambda x: x['timestamp'], reverse=True)

        latest_results = {}
        for doc in sorted_docs:
            model = doc['model']
            if model not in latest_results:
                latest_results[model] = doc

        logging.info(f"Fetched {len(latest_results)} GPT results:")
        for doc in latest_results.values():
            logging.info(f"Model: {doc['model']}, Timestamp: {doc['timestamp']}")

        return list(latest_results.values())

    except Exception as e:
        logging.error(f"Error fetching GPT results: {str(e)}")
        return []

def get_finetune_result(collection):

    try:
        return collection.find_one({
            'model': 'gpt4omini-finetune',
            'timestamp': {'$exists': True},
            'collection_results.meta': {'$exists': True}
        }, sort=[('timestamp', -1)])
    
    except Exception as e:
        logging.error(f"Error fetching finetune result: {str(e)}")
        return None

def process_results(result, reasoning_tasks):

    data = {}

    for task in reasoning_tasks:


        try:
            task_data = result['collection_results'].get(task, {})
            yes = task_data.get('Yes', 0)
            no = task_data.get('No', 0)
            total = yes + no
            percentage = (yes / total) * 100 if total > 0 else 'NA'
            data[task] = {
                'Yes': yes,
                'No': no,
                'Total': total,
                'Percentage': percentage
            }

        except Exception as e:

            logging.error(f"Error processing {task} results: {str(e)}")
            data[task] = {'Yes': 0, 'No': 0, 'Total': 0, 'Percentage': 'NA'}

    return data

def save_to_csv(data, filename):

    try:
        df = pd.DataFrame(data).T
        df.to_csv(filename)
        logging.info(f"Data saved to {filename}")

    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")

def plot_barplot(data, dataset, filename):

    try:
        tasks = ['gpt4omini-meta-ft', 'meta', 'cot', 'decomposition', 'evidence', 'pot', 'faithful']
        models = ['gpt4o', 'gpt4omini']

        percentages = {model: [] for model in models}

        for task in tasks:
            for model in models:

                if model in data and task in data[model]:

                    task_data = data[model][task]
                    yes = task_data.get('Yes', 0)
                    no = task_data.get('No', 0)

                    if yes == 0 and no == 0:
                        percentages[model].append('NA')

                    else:

                        total = yes + no
                        perc = (yes / total) * 100 if total > 0 else 0
                        percentages[model].append(perc)

                else:
                    percentages[model].append('NA')

        x = np.arange(len(tasks))
        width = 0.35

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot bars
        rects1 = ax.bar(x - width/2, [p if p != 'NA' else 0 for p in percentages['gpt4o']], width, label='gpt4o', color='#FF7F7F')
        rects2 = ax.bar(x + width/2, [p if p != 'NA' else 0 for p in percentages['gpt4omini']], width, label='gpt4omini', color='#7FAFFF')

        # Change color of gpt4omini-meta-ft bar
        rects1[0].set_color('#FF4136')
        rects1[0].set_label('gpt4omini-meta-ft')

        ax.set_ylabel('Percentage (%)')
        ax.set_title(f"{dataset.upper()} Percentage/Acc for Different Reasoning Methods")
        ax.set_xticks(x)
        ax.set_xticklabels(tasks, rotation=45, ha='right')
        ax.legend()

        # Set y-axis range
        all_percentages = [p for model in percentages.values() for p in model if p != 'NA']
        if all_percentages:
            y_min = max(0, min(all_percentages) - 5)
            y_max = min(100, max(all_percentages) + 5)
            ax.set_ylim(y_min, y_max)

        # Add labels
        def autolabel(rects, percentages):
            for rect, perc in zip(rects, percentages):
                height = rect.get_height()
                label = 'NA' if perc == 'NA' else f"{perc:.1f}%"
                ax.annotate(label,
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=90)

        autolabel(rects1, percentages['gpt4o'])
        autolabel(rects2, percentages['gpt4omini'])

        fig.tight_layout()

        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Combined barplot saved to {filename}")

    except Exception as e:
        logging.error(f"Error creating combined barplot for {dataset}: {str(e)}")
        logging.debug(f"Data causing error: {data}")

def get_credentials():

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def to_python_type(value):

    if isinstance(value, np.integer):
        return int(value)
    
    elif isinstance(value, np.floating):
        return round(float(value), 2)
    
    elif isinstance(value, np.ndarray):
        return value.tolist()
    
    elif pd.isna(value) or value == 'NA':
        return 'NA'
    else:
        return value


def structure_data_for_sheets(all_results):

    df = pd.DataFrame(all_results)
    structured_data = []
    bold_cells = []
    max_percentage_cells = []
    dataset_cells = []
    model_cells = []
    
    row_index = 0

    for dataset in df['Dataset'].unique():
        structured_data.append([dataset.upper()])
        dataset_cells.append((row_index, 0))
        row_index += 1
        
        structured_data.append(['', 'Yes', 'No', 'Total', 'Percentage'])
        bold_cells.extend([(row_index, i) for i in range(1, 5)])
        row_index += 1
        
        dataset_df = df[df['Dataset'] == dataset]
        
        # Add gpt4omini-meta-ft row only once per dataset
        meta_ft_row = dataset_df[(dataset_df['Model'] == 'gpt4o') & (dataset_df['Task'] == 'gpt4omini-meta-ft')].iloc[0]
        structured_data.append(['gpt4omini-meta-ft'] + [to_python_type(meta_ft_row[col]) for col in ['Yes', 'No', 'Total', 'Percentage']])
        row_index += 1
        
        max_percentage = 0
        max_percentage_row = row_index - 1
        
        for model in ['gpt4o', 'gpt4omini']:

            structured_data.append([model])
            model_cells.append((row_index, 0))
            row_index += 1
            
            model_df = dataset_df[dataset_df['Model'] == model]
            
            for task in ['meta', 'cot', 'decomposition', 'evidence', 'pot', 'faithful']:
                row = model_df[model_df['Task'] == task].iloc[0]
                percentage = to_python_type(row['Percentage'])
                structured_data.append([task] + [to_python_type(row[col]) for col in ['Yes', 'No', 'Total']] + [percentage])
                
                if isinstance(percentage, (int, float)) and percentage > max_percentage:
                    max_percentage = percentage
                    max_percentage_row = row_index
                
                row_index += 1
            
            structured_data.append([''])
            row_index += 1
        
        if max_percentage > 0:
            max_percentage_cells.append((max_percentage_row, 4))
        
        structured_data.append([''])
        row_index += 1
    
    return structured_data, bold_cells, max_percentage_cells, dataset_cells, model_cells

def upload_to_sheet(values, bold_cells, max_percentage_cells, dataset_cells, model_cells):

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:

        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        
        # Upload data
        body = {
            'values': values
        }

        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        RANGE_NAME = "Sheet1!A1:G"

        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption="USER_ENTERED", body=body).execute()
        
        print(f"{result.get('updatedCells')} cells updated.")

        # Apply formatting
        requests = []
        
        for row, col in bold_cells + max_percentage_cells:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": row,
                        "endRowIndex": row + 1,
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            })
        
        for row, col in dataset_cells:

            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": row,
                        "endRowIndex": row + 1,
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True,
                                "fontSize": 12  # Increased font size
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat(bold,fontSize)"
                }
            })
        
        for row, col in model_cells:

            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": row,
                        "endRowIndex": row + 1,
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True,
                                "fontSize": 11  # Increased font size
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat(bold,fontSize)"
                }
            })

        if requests:
            sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()

    except HTTPError as err:
        print(err)


def main():

    client = get_mongodb_client()

    datasets = ['fetaqa', 'finqa', 'sqa', 'hybridqa', 'hitabs', 'multi', 'wiki', 'squall', 'tatqa']
    reasoning_tasks = ['gpt4omini-meta-ft', 'meta', 'cot', 'decomposition', 'evidence', 'pot', 'faithful']

    main_analysis_dir = 'analysis'
    os.makedirs(main_analysis_dir, exist_ok=True)

    all_results = []

    for dataset in datasets:

        try:
            dataset_dir = os.path.join(main_analysis_dir, dataset)
            os.makedirs(dataset_dir, exist_ok=True)

            db = client[dataset]
            results_collection = db['results']

            finetune_result = get_finetune_result(results_collection)
            finetune_data = process_results(finetune_result, ['meta']) if finetune_result else {}

            gpt_results = get_gpt_results(results_collection)

            combined_data = {}

            for result in gpt_results:

                model = result['model']
                data = process_results(result, reasoning_tasks[1:])

                if model == 'gpt4o' and finetune_data:
                    data['gpt4omini-meta-ft'] = finetune_data['meta']

                else:
                    data['gpt4omini-meta-ft'] = {'Yes': 0, 'No': 0, 'Total': 0, 'Percentage': 'NA'}

                ordered_data = {task: data.get(task, {'Yes': 0, 'No': 0, 'Total': 0, 'Percentage': 'NA'}) for task in reasoning_tasks}
                combined_data[model] = ordered_data

                csv_filename = os.path.join(dataset_dir, f"{model}_results.csv")

                save_to_csv(ordered_data, csv_filename)

                for task, task_data in ordered_data.items():

                    all_results.append({
                        'Dataset': dataset,
                        'Model': model,
                        'Task': task,
                        'Yes': task_data.get('Yes', 'NA'),
                        'No': task_data.get('No', 'NA'),
                        'Total': task_data.get('Total', 'NA'),
                        'Percentage': task_data.get('Percentage', 'NA')
                    })

            plot_filename = os.path.join(dataset_dir, f"{dataset}_plot.png")
            plot_barplot(combined_data, dataset, plot_filename)

        except Exception as e:
            logging.error(f"Error processing dataset {dataset}: {str(e)}")

    if all_results:

        combined_df = pd.DataFrame(all_results)
        combined_df = combined_df.sort_values(['Dataset', 'Model', 'Task'])
        combined_csv_filename = os.path.join(main_analysis_dir, 'combined_results.csv')
        combined_df.to_csv(combined_csv_filename, index=False)

        logging.info(f"Combined results saved to {combined_csv_filename}")

        print(combined_df.to_string())

        # Structure data for Google Sheets
        structured_data, bold_cells, max_percentage_cells, dataset_cells, model_cells = structure_data_for_sheets(all_results)

        # Upload to Google Sheets
        upload_to_sheet(structured_data, bold_cells, max_percentage_cells, dataset_cells, model_cells)

    else:
        logging.warning("No results to combine into a DataFrame.")


if __name__ == "__main__":
    main()