# Script to upload the files to the finetune API

from openai import OpenAI

import os 
import argparse

from dotenv import load_dotenv


def submit_finetuning(dataset=None, train=None, val=None):
    #train, val are the file paths

    load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Upload the training data
    if train == None and val == None:
        files = ['train.jsonl', 'validation.jsonl']

        for file in files:

            upload = client.files.create(
                file=open(os.path.join(dataset, file), "rb"),
                purpose="fine-tune"
            )

            print(upload)

        print("Files uploaded successfully")

    else:

        print("Uploading files from the provided paths of train and val")

        upload = client.files.create(
                file=open(train, 'rb'),
                purpose="fine-tune"
            )
        
        print('Train file:', upload)
        
        upload = client.files.create(
                file=open(val, 'rb'),
                purpose="fine-tune"
            )
        
        print('Val file:', upload)


import os
import json

def combine_jsonl_files(input_dir, output_dir, filename):
    combined_data = []
    
    for subdir in os.listdir(input_dir):
        subdir_path = os.path.join(input_dir, subdir)
        if os.path.isdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)
            
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        combined_data.append(json.loads(line.strip()))
    
 
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w') as f:
        for item in combined_data:
            json.dump(item, f)
            f.write('\n')
    
    print(f"Combined {filename} created in {output_dir}")

def finetune(training_file, validation_file, model="gpt-4o-mini-2024-07-18"):

    load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    client.fine_tuning.jobs.create(
        training_file=training_file,
        validation_file=validation_file, 
        model=model
    )

if __name__ == "__main__":

    #How to run this script - 
    # First run this script with the --submit=True flag (without params) to upload the files to the API, 
    # along with the --dataset flag. If you want to run all, use --all=True flag
    # Then run this script with the --train_id and --val_id flags to start the finetuning process
    #To find the train_id and val_id, you can check the output of the previous step (submit file step)

    parser = argparse.ArgumentParser(description='Submit the finetuning files to the API')
    parser.add_argument('--submit', type=bool, help='Name of the training file')
    parser.add_argument('--train_id', type=str, help='Name of the training file')
    parser.add_argument('--val_id', type=str, help='Name of the validation file')
    parser.add_argument('--dataset', type=str, help='Name of the dataset to load')
    parser.add_argument('--all', type=bool, help='All datasets combined. Do not use dataset flag that time')

    args = parser.parse_args()

    if args.submit:
        
        if args.all:
            # Set the input and output directories
            input_dir = 'data'
            output_dir = 'data'

            combine_jsonl_files(input_dir, output_dir, 'train.jsonl')
            combine_jsonl_files(input_dir, output_dir, 'validation.jsonl')

            submit_finetuning(train=os.path.join(output_dir, 'train.jsonl'), val=os.path.join(output_dir, 'validation.jsonl'))

        else:
            submit_finetuning(args.dataset)

    if args.train_id and args.val_id:
        finetune(args.train_id, args.val_id)