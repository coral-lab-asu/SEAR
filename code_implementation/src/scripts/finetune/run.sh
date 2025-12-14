#!/bin/bash

# This shell script will create prompts from all datasets where finetune is set to True
# The script will run the prompts.py script for each dataset in parallel using background processes

# Create logs directory if it doesn't exist
mkdir -p logs

# List of datasets
datasets=(
    "fetaqa"
    "finqa"
    "sqa"
    "hybridqa"
    "multi"
    "squall"
    "tatqa"
    "wiki"
    "hitabs"
)

# Name of the Python script (in the same directory)
python_script="prompts.py"

# Function to run the Python script for a dataset
run_script() {
    dataset=$1
    echo "Starting script for dataset: $dataset"
    python "$python_script" --dataset "$dataset" &> "logs/log_${dataset}.txt" &
    echo "Script started for dataset: $dataset (PID: $!)"
}

# Run the Python script for each dataset in parallel
echo "Processing all datasets in parallel..."
for dataset in "${datasets[@]}"
do
    run_script "$dataset"
done

# Wait for all background processes to complete
echo "Waiting for all processes to complete..."
wait

echo "All datasets have been processed."

# Collect and display logs
echo "Outputs from all datasets:"
for dataset in "${datasets[@]}"
do
    echo "----------------------------------------"
    echo "Output for dataset: $dataset"
    cat "logs/log_${dataset}.txt"
    echo "----------------------------------------"
done