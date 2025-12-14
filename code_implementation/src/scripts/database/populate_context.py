import argparse
import os
import sys
from tqdm import tqdm

# Add the 'models' directory to the system path to import the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(current_dir, '..', 'models')
sys.path.append(models_dir)

import utils

def populate_database(dataset):
    """
    Reads the raw dataset from its source CSV file and populates the 'context'
    collection in the corresponding MongoDB database. This function isolates the
    data loading side-effect of the utils.get_prompts function.
    """
    print(f"Starting data population for dataset: '{dataset}'...")

    # The get_prompts function in utils.py has the side-effect of populating
    # the 'context' collection while it yields prompts. We need to consume
    # the generator it returns to ensure all data is processed and loaded.
    # We pass a dummy reasoning type ('cot') as it's a required argument.
    try:
        prompts_generator = utils.get_prompts(dataset, reasoning='cot')
        
        # Use tqdm to show progress as we iterate through and load the data.
        # The list conversion forces the entire generator to be consumed.
        list(tqdm(prompts_generator, desc=f"Loading '{dataset}' data into MongoDB"))

        print(f"\nData population for dataset '{dataset}' completed successfully.")
        print(f"The 'context' collection in the '{dataset}' database is now populated.")

    except FileNotFoundError:
        print(f"\nError: The source data file for the '{dataset}' dataset was not found.")
        print(f"Please ensure 'data/{dataset}/test.csv' exists.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate the MongoDB 'context' collection from a source CSV file."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        type=str,
        help="The name of the dataset to process (e.g., fetaqa, wiki)."
    )
    args = parser.parse_args()

    populate_database(args.dataset)