#!/bin/bash

# Prompt user for max_workers and sample_size
read -p "Enter the value for max_workers: " max_workers
# read -p "Enter the value for sample_size: " sample_size

# Define arrays for models, datasets, and reasoning types
models=("gemini")
datasets=("wiki" "multi" "hitabs")
reasonings=("meta_3_step" "imp_meta_3_step")

# Iterate through combinations and execute the command
for model in "${models[@]}"; do
  for dataset in "${datasets[@]}"; do
    for reasoning in "${reasonings[@]}"; do
      echo "Running: python three_step_gemini.py --model $model --dataset $dataset --reasoning $reasoning --sample_size $sample_size --max_workers $max_workers"
      python three_step_gemini.py --model "$model" --dataset "$dataset" --reasoning "$reasoning" --max_workers "$max_workers"
    done
  done
done

echo "All commands executed."
