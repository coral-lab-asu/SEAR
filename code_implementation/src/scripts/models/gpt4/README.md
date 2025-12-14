# GPT Family Batch Request Pipeline

This repository contains a pipeline for submitting batch requests to GPT family models, processing the results, and storing them in MongoDB.

## Overview

The `run.sh` script orchestrates the entire pipeline, running multiple Python scripts to handle different stages:

1. Prompt construction (`prompts.py`)
2. Batch request submission (`batch.py`)
3. Result retrieval and MongoDB upload (`process_results.py`)

## Usage

```
./run.sh -d <datasets> -m <models> -r <reasonings>
```

### Required Arguments

- `-d`: Comma-separated list of datasets
- `-m`: Comma-separated list of models
- `-r`: Comma-separated list of reasoning methods

## Example

To run fetaqa, finqa, and sqa on GPT4omini using POT and COT reasoning:

```
./run.sh -d fetaqa,finqa,sqa -m gpt-4o-mini -r pot,cot
```

For a finetuned model, use the full model name:

```
./run.sh -d fetaqa -m ft:gpt-4o-mini-2024-07-18:cogcomp::A1SErUg0 -r meta-finetune
```

## Pipeline Steps

1. **Prompt Construction**: Generates prompts using `prompts.py`
2. **Batch Request Submission**: Submits batch requests using `batch.py`
3. **Result Processing**: Retrieves results and uploads to MongoDB using `process_results.py`

## Parallel Execution

If multiple datasets and reasoning methods are provided, the requests will be sent in parallel to improve efficiency.

## Individual Script Usage

To run individual scripts, refer to each script and its specific arguments:

- `python prompts.py --dataset <dataset> --reasoning <reasoning> --model <model>`
- `python batch.py --dataset <dataset> --model <model> --reasoning <reasoning>`
- `python process_results.py --datasets <dataset> --response_model <model> --reasonings <reasoning>`

## Requirements

- Python 3.x
- Required Python packages (install via `pip install -r requirements.txt`)
- Bash shell
- MongoDB (for result storage)

## Notes

- Ensure you have the necessary API keys and MongoDB connection details set up before running the pipeline.
- The script creates a comprehensive log of its operations, making it easy to track progress and diagnose issues.
