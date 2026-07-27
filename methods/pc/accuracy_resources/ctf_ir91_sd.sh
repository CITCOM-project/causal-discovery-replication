#!/bin/bash
#SBATCH --job-name=ctf_ir91_sd
#SBATCH --output=logs/ctf_ir91_sd/output_%A_%a.txt
#SBATCH --error=logs/ctf_ir91_sd/error_%A_%a.txt
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --array=0-119

source /opt/apps/testapps/common/software/staging/Anaconda3/2024.02-1/etc/profile.d/conda.sh
conda activate pc-env

ALPHA=(0.01 0.05 0.1 0.2)
RANDOM_SEEDS=(10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250 260 270 280 290 300)

VAL_INDEX=$(( SLURM_ARRAY_TASK_ID / 30 ))
SEED_INDEX=$(( SLURM_ARRAY_TASK_ID % 30 ))
val=${ALPHA[$VAL_INDEX]}
seed=${RANDOM_SEEDS[$SEED_INDEX]}

OUTPUT_FILE="data/ctf/pc_ir91_sd/output_pc_alpha_${val}_seed_${seed}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running causal-testing with alpha=${val} and random_seed=${seed}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v python run_pc.py \
    -d data/ctf/ir91.csv \
    -o "$OUTPUT_FILE" \
    -a $val \
    --seed "$seed" \
    -V G_Na max_voltage max_voltage_gradient dome_voltage APD50 G_si rest_voltage APD90 G_K G_K1 G_Kp G_b

echo "======================================================"
echo "Run for alpha=${val} and random_seed=${seed} completed."