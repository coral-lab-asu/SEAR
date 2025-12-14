# Models Directory

## Overview

This directory contains the scripts and configurations necessary to run the reasoning tasks for various datasets using different models such as GPT, Gemini, and open-source models on Groq. Following the description from the main README, the tasks in this directory are designed to process and evaluate datasets with specific reasoning approaches.

## Usage

### Running GPT Models

To run the reasoning tasks using GPT models, navigate to the `gpt4` directory and follow the instructions provided in the corresponding README file.

### Running Gemini

To run reasoning tasks using Gemini, use the `gemini_workers.py` script. This script facilitates the execution of tasks across multiple datasets and reasoning methods. The script supports the following arguments:

#### Arguments and Usage

- **`--dataset`** (type: `str`, default: `'fetaqa'`):
  - Specifies the dataset to be used for the reasoning task.
  - Example: `--dataset hybridqa` to use the HybridQA dataset.

- **`--reasoning`** (type: `str`, default: `'COT'`):
  - Determines the reasoning method to be applied. This could include options like Chain of Thought (`COT`), Program of Thought (`POT`), or others as defined in the project.
  - Example: `--reasoning POT` to use the Program of Thought reasoning method.

- **`--rows`** (type: `int`, default: `5000`):
  - Specifies the number of rows (or data points) to generate or process from the dataset.
  - Example: `--rows 1000` to generate 1000 rows.

- **`--random`** (type: `bool`, default: `False`):
  - If set to `True`, the script will randomly select rows to generate or process.
  - Example: `--random True` to enable random row selection.

- **`--meta`** (type: `bool`, default: `False`):
  - When enabled, this flag generates meta prompts, which might be used for specific meta-reasoning tasks.
  - **Important**: When using the `reasoning` flag, do not use the `meta` flag. If you want to run meta reasoning, set the `reasoning` argument to `'meta'`.
  - Example: `--meta True` to generate meta prompts.

- **`--from_index`** (type: `int`, default: `0`):
  - Indicates the starting index for row generation or processing. This is useful if you need to process a specific subset of data.
  - Example: `--from_index 100` to start processing from the 100th row.

- **`--max_workers`** (type: `int`, default: `5`):
  - Sets the maximum number of concurrent workers to be used during task execution. This controls the level of parallelism and can be adjusted based on the available resources.
  - Example: `--max_workers 10` to run with up to 10 concurrent workers.

### Running Gemini in Agentic Mode

To run Gemini in agentic mode, use the `gemini_workers_agentic2.py` script with similar arguments as for `gemini_workers.py`. 

- **Gemini Agentic** is an agentic system that we are developing, which takes the entire meta-reasoning prompt and provides specific instructions to other Gemini agents based on the table and the question. This interaction represents a more autonomous, agent-driven approach.

### Example Command

Here’s an example command to run the `gemini_workers.py` script with custom arguments:

```bash
python gemini_workers.py --dataset hybridqa --reasoning POT --rows 1000 --random True --from_index 50 --max_workers 10
```

This command would run the Gemini reasoning task on the HybridQA dataset using the Program of Thought reasoning method, processing 1000 rows starting from the 50th row, selecting rows randomly, and utilizing up to 10 workers concurrently.

For meta reasoning:

```bash
python gemini_workers.py --dataset hybridqa --reasoning meta --rows 1000 --random True --from_index 50 --max_workers 10
```

This command would run the Gemini task with meta reasoning on the HybridQA dataset.

## Additional Information

For further instructions on running specific models or understanding the structure of this directory, refer to the `README.md` files located within each subdirectory.
