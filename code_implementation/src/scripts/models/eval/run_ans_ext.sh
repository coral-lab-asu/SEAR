#!/bin/bash
#SBATCH --account soc-gpu-np
#SBATCH --partition soc-gpu-np
#SBATCH --ntasks-per-node=16
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --mem=32GB
#SBATCH -o ans_extract-%j
#SBATCH --export=ALL

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/uufs/chpc.utah.edu/common/home/u1472614/miniconda3/lib
export MODEL='gemini'
export DATASET='squall'
export REASONING='all'

source ~/miniconda3/etc/profile.d/conda.sh
conda activate base

python extract_answer.py --dataset $DATASET --model $MODEL --reasoning $REASONING

