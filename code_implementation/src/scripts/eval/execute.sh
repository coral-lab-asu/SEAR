#!/bin/bash

# read -p "Enter the value for sample_size: " sample_size

# Define arrays for models, datasets, and reasoning types
models=("gemini")
datasets=("wiki" "multi" "hitabs" "finqa" "tatqa" "squall" "fetaqa" "hybridqa")
reasonings=("meta_3_step" "clean_meta_3_step")

# Iterate through combinations and execute the command
for model in "${models[@]}"; do
  for dataset in "${datasets[@]}"; do
    for reasoning in "${reasonings[@]}"; do
      echo "Running: /run.sh --rm $model --e $model --d $dataset --r $reasoning --tag feb_13_2025"
      ./run.sh --rm "$model" --e "$model" --d "$dataset" --r "$reasoning" --tag feb_13_2025
    done
  done
done

echo "All commands executed."
