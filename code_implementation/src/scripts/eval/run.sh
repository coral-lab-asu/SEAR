#!/bin/zsh

# Script to run prompt generation and evaluation with multiple datasets and reasoning methods

# Examples:
# 1. Run for specific datasets and reasoning methods:
#    ./run.sh --rm gpt4o --e gemini --d fetaqa,finqa --r cot,pot,meta
#
# 2. Run for all datasets with specific reasoning methods:
#    ./run.sh --rm gpt4o --e gemini --d all --r cot,pot,meta
#
# 3. Run with a sample size, optional plotting, and tag:
#    ./run.sh --rm gpt4omini --e gemini --d fetaqa --r cot,pot,meta --s 100 --p --tag experiment1

# Function to display usage information
usage() {
    echo "Usage: $0 --rm <response_model> --e <evaluator> --d <datasets> --r <reasoning_methods> [--s <sample>] [--p] [--tag <tag>]"
    echo "Example: $0 --rm gpt4o --e gemini --d fetaqa,finqa --r cot,pot,meta"
    echo "Example with all datasets: $0 --rm gpt4o --e gemini --d all --r cot,pot,meta"
    echo "Example with optional sample, plotting, and tag: $0 --rm gpt4omini --e gemini --d fetaqa --r cot,pot,meta --s 100 --p --tag experiment1"
    echo "  --rm: Response model to evaluate (gpt4o, gpt4omini or gemini)"
    echo "  --e: Evaluator model (e.g., gemini)"
    echo "  --d: Comma-separated list of datasets or 'all' for all datasets"
    echo "  --r: Comma-separated list of reasoning methods"
    echo "  --s: (Optional) Number of samples to evaluate (default: 0, meaning all)"
    echo "  --p: (Optional) Generate plots after evaluation"
    echo "  --tag: (Optional) Tag for the results"
}

# Initialize variables
RESPONSE_MODEL=""
EVALUATOR=""
DATASETS=""
REASONING_METHODS=""
SAMPLE=0
MAX_WORKERS=5
PLOT=false
TAG=""

# All available datasets
ALL_DATASETS="fetaqa,finqa,sqa,hybridqa,hitabs,squall,wiki,multi,tatqa"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rm) RESPONSE_MODEL="$2"; shift 2 ;;
        --e) EVALUATOR="$2"; shift 2 ;;
        --d) DATASETS="$2"; shift 2 ;;
        --r) REASONING_METHODS="$2"; shift 2 ;;
        --s) SAMPLE="$2"; shift 2 ;;
        --p) PLOT=true; shift ;;
        --tag) TAG="$2"; shift 2 ;;
        *) echo "Unknown parameter passed: $1"; usage; exit 1 ;;
    esac
done

# Check if required arguments are provided
if [ -z "$RESPONSE_MODEL" ] || [ -z "$EVALUATOR" ] || [ -z "$DATASETS" ] || [ -z "$REASONING_METHODS" ]; then
    echo "Error: Missing required arguments"
    usage
    exit 1
fi

# Handle 'all' datasets option
if [ "$DATASETS" = "all" ]; then
    DATASETS="$ALL_DATASETS"
fi

# Convert comma-separated strings to arrays
IFS=',' read -A DATASET_ARRAY <<< "$DATASETS"
IFS=',' read -A REASONING_ARRAY <<< "$REASONING_METHODS"

# Main execution loop
for DATASET in "${DATASET_ARRAY[@]}"; do
    echo "Processing dataset: $DATASET"

    # Run extract_answer.py
    echo "Extracting answers..."
    python extract_answer.py --model $RESPONSE_MODEL --dataset $DATASET --reasoning ${(q)REASONING_ARRAY[@]}
    echo "Answers extracted successfully."

    # Run prompt.py
    echo "Generating prompts..."
    python prompt.py --response_model $RESPONSE_MODEL --dataset $DATASET --reasoning ${(q)REASONING_ARRAY[@]} --sample $SAMPLE --evaluator $EVALUATOR --run_all

    # Check if prompt.py executed successfully
    if [ $? -ne 0 ]; then
        echo "Error: prompt.py failed to execute properly for dataset $DATASET."
        continue
    fi

    echo "Generating reasoning paths analysis"
    python get_reasoning_path.py --dataset $DATASET --model $RESPONSE_MODEL
    echo "Reasoning paths analysis generated successfully."

    # Run evaluate.py
    echo "Running evaluation with $EVALUATOR..."

    python evaluate_responses.py --evaluator $EVALUATOR --response_model $RESPONSE_MODEL --dataset $DATASET --reasoning ${(q)REASONING_ARRAY[@]} --max_workers $MAX_WORKERS

    # Check if evaluate.py executed successfully
    if [ $? -ne 0 ]; then
        echo "Error: evaluate_responses.py failed to execute properly for $EVALUATOR on dataset $DATASET."
        continue
    fi

    echo "Processing results..."
    if [ -n "$TAG" ]; then
        python results.py --model $RESPONSE_MODEL --dataset $DATASET --evaluator $EVALUATOR --tag "$TAG"
    else
        python results.py --model $RESPONSE_MODEL --dataset $DATASET --evaluator $EVALUATOR
    fi
    echo "Results processed successfully."

    echo "Evaluation pipeline completed for dataset: $DATASET"
    echo "----------------------------------------"
done

echo "All datasets have been processed."

# Optional plotting
if $PLOT; then
    echo "Plotting graphs and analysing GPT results..."
    python plot.py
fi

echo "Evaluation pipeline completed successfully."