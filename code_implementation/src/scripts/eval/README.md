# Evaluation Pipeline

This repository contains a comprehensive pipeline for generating prompts, extracting answers, and evaluating responses across multiple datasets and reasoning methods using various language models.

## Overview

The `run.sh` script orchestrates the entire process, running multiple Python scripts to handle different stages of the pipeline:

1. Answer extraction
2. Prompt generation
3. Reasoning path analysis
4. Evaluation
5. Results processing
6. Optional plotting

## Usage

```
./run.sh --rm <response_model> --e <evaluator> --d <datasets> --r <reasoning_methods> [--s <sample>] [--p] [--tag <tag>]
```

### Required Arguments

- `--rm`: Response model to evaluate (gpt4o, gpt4omini, or gemini)
- `--e`: Evaluator model (e.g., gemini)
- `--d`: Comma-separated list of datasets or 'all' for all datasets
- `--r`: Comma-separated list of reasoning methods

### Optional Arguments

- `--s`: Number of samples to evaluate (default: 0, meaning all)
- `--p`: Generate plots after evaluation
- `--tag`: Tag for the results

## Examples

1. Run for specific datasets and reasoning methods:
   ```
   ./run.sh --rm gpt4o --e gemini --d fetaqa,finqa --r cot,pot,meta
   ```

2. Run for all datasets with specific reasoning methods:
   ```
   ./run.sh --rm gpt4o --e gemini --d all --r cot,pot,meta
   ```

3. Run with a sample size, optional plotting, and tag:
   ```
   ./run.sh --rm gpt4omini --e gemini --d fetaqa --r cot,pot,meta --s 100 --p --tag experiment1
   ```

4. To run the evaluation for GPT4omini finetuned model
   ```
   ./run.sh --rm gpt4omini-finetune --e gemini --d fetaqa --r meta --tag experiment1
   ```


## Available Datasets

fetaqa, finqa, sqa, hybridqa, hitabs, squall, wiki, multi, tatqa

## Pipeline Steps

1. **Answer Extraction**: Extracts answers using `extract_answer.py`
2. **Prompt Generation**: Generates prompts using `prompt.py`
3. **Reasoning Path Analysis**: Analyzes reasoning paths using `get_reasoning_path.py`
4. **Evaluation**: Evaluates responses using `evaluate.py`
5. **Results Processing**: Processes results using `results.py`
6. **Optional Plotting**: Generates plots using `plot.py` if the `--p` flag is set

## Notes

- The script uses a maximum of 8 workers for parallel processing during evaluation.
- If any step fails for a particular dataset, the script will continue with the next dataset.
- The script creates a comprehensive log of its operations, making it easy to track progress and diagnose issues.

## Requirements

- Python 3.x
- Required Python packages (install via `pip install -r requirements.txt`)
- Zsh shell
