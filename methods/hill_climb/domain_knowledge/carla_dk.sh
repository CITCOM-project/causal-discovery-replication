#!/bin/bash
#SBATCH --job-name=carla_dk
#SBATCH --output=logs/carla_dk/output_%A_%a.txt
#SBATCH --error=logs/carla_dk/error_%A_%a.txt
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --array=0-299

source /opt/apps/testapps/common/software/staging/Anaconda3/2024.02-1/etc/profile.d/conda.sh
conda activate ctf-env

PERCENTS=(1 3 5 10 15 20 25 30 40 50)
RANDOM_SEEDS=(10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250 260 270 280 290 300)

PERCENT_INDEX=$(( SLURM_ARRAY_TASK_ID / 30 ))
SEED_INDEX=$(( SLURM_ARRAY_TASK_ID % 30 ))
percent=${PERCENTS[$PERCENT_INDEX]}
seed=${RANDOM_SEEDS[$SEED_INDEX]}
alpha=0.01

OUTPUT_FILE="data/carla/hc_dk/output_hc_percent_${percent}_seed_${seed}_alpha_${alpha}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running HC Algorithm with random_seed=${seed} and percent =${percent}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v causal-testing discover \
    -t HillClimberDiscovery \
    -c -d data/carla/garage_privileged_data_pro.csv data/carla/garage_trained_data_pro.csv data/carla/TCP_privileged_data_pro.csv data/carla/TCP_trained_data_pro.csv \
    -o "$OUTPUT_FILE" \
    -a $alpha \
    -e "partials/carla_percent_${percent}_seed_${seed}_excluded.dot" \
    -i "partials/carla_percent_${percent}_seed_${seed}_included.dot" \
    --technique-kwargs random_seed="$seed"

echo "======================================================"
echo "Run for random_seed=${seed} percent=${percent} completed."