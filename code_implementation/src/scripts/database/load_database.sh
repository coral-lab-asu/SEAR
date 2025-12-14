cd /home/mvyas7/SEAR/TempTab-Recasting/src/scripts/database

# Define your datasets
DATASETS="fetaqa finqa hitab hybridqa multi squall tatqa wiki"

# Path to your existing NoT prompts
NOT_PROMPTS_DIR="/home/mvyas7/SEAR/TempTab-Recasting/src/scripts/database/NoT_promts"

# Upload to each dataset
for DATASET in $DATASETS; do
    echo "Uploading NoT prompt to $DATASET..."
    python prompts.py --dataset $DATASET --directory $NOT_PROMPTS_DIR
done