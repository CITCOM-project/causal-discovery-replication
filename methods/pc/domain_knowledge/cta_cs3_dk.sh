#!/bin/bash
#SBATCH --job-name=cta_cs3_dk
#SBATCH --output=logs/cta_cs3_dk/output_%A_%a.txt
#SBATCH --error=logs/cta_cs3_dk/error_%A_%a.txt
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --array=0-299

source /opt/apps/testapps/common/software/staging/Anaconda3/2024.02-1/etc/profile.d/conda.sh
conda activate pc-env

PERCENTS=(1 3 5 10 15 20 25 30 40 50)
RANDOM_SEEDS=(10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250 260 270 280 290 300)

PERCENT_INDEX=$(( SLURM_ARRAY_TASK_ID / 30 ))
SEED_INDEX=$(( SLURM_ARRAY_TASK_ID % 30 ))
percent=${PERCENTS[$PERCENT_INDEX]}
seed=${RANDOM_SEEDS[$SEED_INDEX]}
alpha=0.2

OUTPUT_FILE="data/cta/pc_dk_cs3/output_pc_percent_${percent}_seed_${seed}_alpha_${alpha}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running PC Algorithm with random_seed=${seed} and percent =${percent}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v python pc.py \
    -d data/cta/cs3_data/data_10000_1.csv data/cta/cs3_data/data_10000_2.csv data/cta/cs3_data/data_10000_3.csv data/cta/cs3_data/data_10000_4.csv \
        data/cta/cs3_data/data_10000_5.csv data/cta/cs3_data/data_10000_6.csv data/cta/cs3_data/data_10000_7.csv data/cta/cs3_data/data_10000_8.csv \
        data/cta/cs3_data/data_10000_9.csv data/cta/cs3_data/data_10000_10.csv data/cta/cs3_data/data_10000_11.csv data/cta/cs3_data/data_10000_12.csv \
        data/cta/cs3_data/data_10000_13.csv data/cta/cs3_data/data_10000_14.csv data/cta/cs3_data/data_10000_15.csv data/cta/cs3_data/data_10000_16.csv \
        data/cta/cs3_data/data_10000_17.csv data/cta/cs3_data/data_10000_18.csv data/cta/cs3_data/data_10000_19.csv data/cta/cs3_data/data_10000_20.csv \
        data/cta/cs3_data/data_10000_21.csv data/cta/cs3_data/data_10000_22.csv data/cta/cs3_data/data_10000_23.csv data/cta/cs3_data/data_10000_24.csv \
        data/cta/cs3_data/data_10000_25.csv data/cta/cs3_data/data_10000_26.csv data/cta/cs3_data/data_10000_27.csv data/cta/cs3_data/data_10000_28.csv \
        data/cta/cs3_data/data_10000_29.csv data/cta/cs3_data/data_10000_30.csv \
    -o "$OUTPUT_FILE" \
    -t data/cta/cs3_truth.dot \
    -a "$alpha" \
    -p "$percent" \
    --seed "$seed" \
    -V mortality_prob recovery_time mortality_time transmission_prob encounter_rate incubation_time total_infected

echo "======================================================"
echo "Run for random_seed=${seed} percent=${percent} completed."