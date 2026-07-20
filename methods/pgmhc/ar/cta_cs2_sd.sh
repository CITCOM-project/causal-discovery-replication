#!/bin/bash
#SBATCH --job-name=cta_cs2_sd
#SBATCH --output=logs/cta_cs2_sd/output_%A_%a.txt
#SBATCH --error=logs/cta_cs2_sd/error_%A_%a.txt
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --array=0-29

source /opt/apps/testapps/common/software/staging/Anaconda3/2024.02-1/etc/profile.d/conda.sh
conda activate ges_env

RANDOM_SEEDS=(10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250 260 270 280 290 300)

SEED_INDEX=$(( SLURM_ARRAY_TASK_ID))
seed=${RANDOM_SEEDS[$SEED_INDEX]}

OUTPUT_FILE="data/cta/pgmhc_sd_cs2/output_pgmhc_seed_${seed}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running pgmhc Algorithm with random_seed=${seed}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v python hc.py \
    -d data/cta/cs2_data.csv \
    -o "$OUTPUT_FILE" \
    --seed "$seed" \
    -V pop_size contacts location susceptibility cum_infections

echo "======================================================"
echo "Run for random_seed=${seed} completed."