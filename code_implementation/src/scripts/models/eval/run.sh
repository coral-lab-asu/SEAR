#!/bin/bash
#SBATCH --account soc-gpu-np
#SBATCH --partition soc-gpu-np
#SBATCH --ntasks-per-node=32
#SBATCH --nodes=1
#SBATCH --gres=gpu
#SBATCH --time=5:00:00
#SBATCH --mem=40GB
#SBATCH --mail-user=u1471428@utah.edu
#SBATCH --mail-type=FAIL,END
#SBATCH -o assignment_1-%j
#SBATCH --export=ALL
source ~/miniconda3/etc/profile.d/conda.sh
conda activate mapqa

python extract_answer.py --dataset=wiki --reasoning=meta  --model=gemini-3-steps