Here's a good README file based on the description provided:

# GPT4omini Finetuning

This repository contains scripts and tools for finetuning GPT4omini using custom prompts.

## Contents

1. `prompts.py`: Handles the logic to fetch finetuning prompts from the MongoDB collection.
2. `run.sh`: Creates the prompts files for finetuning, which are saved in the `data` directory. Runs the prompts.py in a loop for all datasets
3. `submit.py`: Submits files to OpenAI and initiates finetuning jobs.

## Usage

### Creating Prompt Files

To create prompt files for finetuning:

```
./run.sh
```

This will generate prompt files in the `data` directory.

### Submitting Files and Finetuning Jobs

Use `submit.py` to upload files to the OpenAI API and submit finetuning jobs. The script has two main functions:

1. Submitting files
2. Initiating finetuning jobs

#### Submitting Files

To submit files to the OpenAI API:

```
python submit.py --submit=True --dataset=<dataset_name>
```

To submit all datasets:

```
python submit.py --submit=True --all=True
```

This step will output `train_id` and `val_id` for each submitted file. Note these IDs for the next step.

#### Initiating Finetuning Jobs

After submitting files, use the obtained `train_id` and `val_id` to start the finetuning process:

```
python submit.py --train_id=<train_id> --val_id=<val_id>
```

Replace `<train_id>` and `<val_id>` with the actual IDs obtained from the file submission step.

## Examples

1. Submitting a specific dataset:
   ```
   python submit.py --submit=True --dataset=my_custom_dataset
   ```

2. Submitting all datasets:
   ```
   python submit.py --submit=True --all=True
   ```

3. Initiating a finetuning job:
   ```
   python submit.py --train_id=file-abc123 --val_id=file-xyz789
   ```

## Notes

- Ensure you have the necessary permissions and API keys set up for OpenAI.
- The `data` directory should exist and be writable.
- MongoDB connection details should be properly configured in `prompts.py`.

For more information or troubleshooting, please refer to the individual script documentation or contact the repository maintainer.