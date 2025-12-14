# TempTab Meta Prompting

## Overview

TempTab Meta Prompting is a project focused on developing a robust system that can effectively handle various types of questions across multiple temporal tabular QA datasets. The project deals with 9 temporal tabular QA datasets, including FetaQA, HybridQA, Squall, among others.

The primary goal is to establish baselines for Gemini and the GPT family using different reasoning methods such as Chain of Thought (CoT), Program of Thought (PoT), Decomposition, Evidence Extraction, and Faithful Chain of Thought. The initial results indicated below-par performance across the datasets, prompting the development of a unified system. This system leverages both prompting and fine-tuning approaches to handle diverse questions more effectively.

## Installation

To set up the project, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kushagraDixit/TempTab-Recasting.git
   cd TempTab-Recasting
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   > **Note**: The `requirements.txt` file may be incomplete. If you encounter any missing dependencies while running the scripts, install them using `pip install <package-name>` and then update the `requirements.txt` file by running:
   > ```bash
   > pip freeze > requirements.txt
   > ```

4. **Environment Variables**:
   - Create a `.env` file in the root directory of the project. This file should contain the necessary credentials for the project, including:
     ```plaintext
     GEMINI_API_KEY2=your_gemini_api_key
     OPENAI_API_KEY=your_openai_api_key
     MONGODB_URI=your_mongodb_atlas_uri
     SPREADSHEET_ID=your_google_sheets_id
     ```
   - This file is essential for accessing APIs and for storing results in the cloud database.

## Usage

- **General Tip**:
  - Most of the functionalities are executed using a `run.sh` script for each task. For specific instructions on running a particular task, consult the `README.md` in the respective directory.

- **Fine-tuning, Evaluation, and Submitting Requests**: 
  - To fine-tune models, run evaluations, or submit requests to GPT in batch mode, navigate to the appropriate directories under `src/scripts/`. Each of these tasks has its own dedicated directory and associated scripts.
  
- **Running GPT Models**:
  - To run GPT models, go to `src/scripts/models/gpt4` and follow the instructions there.

- **Running Gemini**:
  - To run Gemini, use the `gemini_workers.py` script located in `src/scripts/models`.
  - To run Gemini in agentic mode, use the `gemini_workers_agentic2.py` script in the same directory.

- **Directory-Specific Instructions**:
  - If any directory contains a `README.md` file, please follow the instructions provided in that document.

## Results Storage

- The results from various tasks and experiments are stored in a MongoDB Atlas cloud database. Ensure that your `.env` file includes the `MONGODB_URI` for proper data persistence.

### Helpful Tips:

- **If your results are stored in CSV**:
  - First, check the `database` directory to learn how to store the results in MongoDB Atlas. This will ensure that the project flows as expected.
  - Be sure to read the `README` guide in the `database` directory for detailed instructions.

- **If your results are already stored in MongoDB**:
  - You can proceed with the project as you are. No additional steps are needed.

- **Prompts Storage**:
  - Ensure that all prompts for reasoning methods are uploaded to MongoDB under each dataset's prompts collection.
  - Each prompt should be stored with the following keys: `system`, `user`, and `reasoning`. This organization will help in efficiently managing and retrieving prompts during processing.

## How to run this project end to end
### Example of GPT4omini Finetuning

**Getting prompts for finetuning** - Ensure that the responses in the collection of each dataset is tagged with 'finetune: true' for the responses you want to use for finetuning the model. 

1. Run the ./run.sh in ```src/scripts/finetune``` directory to build the prompts for finetuning

Follow the README in the /finetune for specific and detailed instructions on constructing the submitting the finetuning job


2. Run the ./run.sh in ```src/scripts/models/gpt4 ``` directory to submit batch requests to OpenAI

``` ./run.sh -d tatqa -m ft:gpt-4o-mini-2024-07-18:cogcomp::A3Ac8XIh -r meta-finetune ```
When submitting the batch request with the finetuned model, use the full finetuned model name.
Refer to the README in /gpt4 for more detailed instructions. The reasoning argument must be 'meta-finetune' to use with the finetuned model. 

3. Run the ./run.sh in ```src/scripts/eval/ ``` directory to get the results of evaluation

``` ./run.sh --rm gpt4omini-finetune --e gemini --d tatqa --r meta --tag 'ind' ```

When running the evaluation for the finetuned model, use the response model as 'gpt4omini-finetune' and reasoning 'meta'. The tag 'ind' refers to the finetuning done on individual datasets. The tag is used to identify the results for a particular run. 

## Contributing

To contribute to this project, please contact the developer directly and fork the project. Contributions are welcomed through pull requests after discussion with the project maintainer.

## Acknowledgements

This project was developed with support from the University of Pennsylvania (UPenn). Their assistance and resources were instrumental in the successful completion of this work.

