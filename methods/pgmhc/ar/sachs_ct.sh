#!/bin/bash
#SBATCH --job-name=sachs_ct
#SBATCH --output=logs/sachs_ct/output_%A_%a.txt
#SBATCH --error=logs/sachs_ct/error_%A_%a.txt
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

OUTPUT_FILE="data/sachs/pgmhc_ct/output_pgmhc_seed_${seed}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running pgmhc Algorithm with random_seed=${seed}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v python hc.py \
    -c -d data/sachs/b2camp.csv data/sachs/cd3cd28_aktinhib.csv data/sachs/cd3cd28_g0076.csv data/sachs/cd3cd28_icam2.csv \
        data/sachs/cd3cd28_ly.csv data/sachs/cd3cd28_psitect.csv data/sachs/cd3cd28_u0126.csv \
        data/sachs/cd3cd28.csv data/sachs/cd3cd28icam2_aktinhib.csv data/sachs/cd3cd28icam2_g0076.csv \
        data/sachs/cd3cd28icam2_ly.csv data/sachs/cd3cd28icam2_psit.csv data/sachs/cd3cd28icam2_u0126.csv \
        data/sachs/pma.csv \
    -o "$OUTPUT_FILE" \
    --seed "$seed" \
    -V PKA Jnk PKC P38 Akt PIP3 Erk Mek Raf PIP2 Plcg

echo "======================================================"
echo "Run for random_seed=${seed} completed."