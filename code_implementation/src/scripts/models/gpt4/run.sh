#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -d <datasets> -m <models> -r <reasonings>"
    echo "  -d: Comma-separated list of datasets"
    echo "  -m: Comma-separated list of models"
    echo "  -r: Comma-separated list of reasoning methods"
    echo "Example: $0 -d fetaqa,finqa -m gpt4o,gpt-3.5-turbo -r cot,pot"
    exit 1
}

# Parse command-line arguments
while getopts ":d:m:r:" opt; do
    case $opt in
        d) DATASETS="$OPTARG" ;;
        m) MODELS="$OPTARG" ;;
        r) REASONINGS="$OPTARG" ;;
        \?) echo "Invalid option -$OPTARG" >&2; usage ;;
    esac
done

# Check if all required arguments are provided
if [ -z "$DATASETS" ] || [ -z "$MODELS" ] || [ -z "$REASONINGS" ]; then
    echo "Error: Missing required arguments"
    usage
fi

# Function to run the pipeline for a single combination
run_pipeline() {
    local dataset=$1
    local model=$2
    local reasoning=$3

    echo "Running pipeline for dataset: $dataset, model: $model, reasoning: $reasoning"

    # Run prompts.py
    python prompts.py --dataset "$dataset" --reasoning "$reasoning" --model "$model"

    # Run batch.py
    python batch.py --dataset "$dataset" --model "$model" --reasoning "$reasoning"

    # Run process_results.py
    python process_results.py --datasets "$dataset" --response_model "$model" --reasonings "$reasoning"
}

# Main execution
IFS=',' read -ra DATASET_ARRAY <<< "$DATASETS"
IFS=',' read -ra MODEL_ARRAY <<< "$MODELS"
IFS=',' read -ra REASONING_ARRAY <<< "$REASONINGS"

# Use a simple form of job control to run tasks in parallel
for dataset in "${DATASET_ARRAY[@]}"; do
    for model in "${MODEL_ARRAY[@]}"; do
        for reasoning in "${REASONING_ARRAY[@]}"; do
            run_pipeline "$dataset" "$model" "$reasoning" &
        done
    done
done

# Wait for all background jobs to finish
wait

echo "Pipeline execution completed."