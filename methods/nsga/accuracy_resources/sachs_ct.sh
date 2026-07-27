#!/bin/bash
#SBATCH --job-name=sachs_ct
#SBATCH --output=logs/sachs_ct/output_%A_%a.txt
#SBATCH --error=logs/sachs_ct/error_%A_%a.txt
#SBATCH --time=00:35:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --array=0-119

source /opt/apps/testapps/common/software/staging/Anaconda3/2024.02-1/etc/profile.d/conda.sh
conda activate ctf-env

ALPHA=(0.01 0.05 0.1 0.2)
RANDOM_SEEDS=(10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250 260 270 280 290 300)

VAL_INDEX=$(( SLURM_ARRAY_TASK_ID / 30 ))
SEED_INDEX=$(( SLURM_ARRAY_TASK_ID % 30 ))
val=${ALPHA[$VAL_INDEX]}
seed=${RANDOM_SEEDS[$SEED_INDEX]}

OUTPUT_FILE="data/sachs/nsga_ct/output_nsga_alpha_${val}_seed_${seed}.dot"

echo "======================================================"
echo "Master Job ID: $SLURM_ARRAY_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running causal-testing with alpha=${val} and random_seed=${seed}"
echo "Output will be saved to: ${OUTPUT_FILE}"
echo "======================================================"

/usr/bin/time -v causal-testing discover \
    -t NSGADiscovery \
    -c -d data/sachs/b2camp.csv data/sachs/cd3cd28_aktinhib.csv data/sachs/cd3cd28_g0076.csv data/sachs/cd3cd28_icam2.csv \
        data/sachs/cd3cd28_ly.csv data/sachs/cd3cd28_psitect.csv data/sachs/cd3cd28_u0126.csv \
        data/sachs/cd3cd28.csv data/sachs/cd3cd28icam2_aktinhib.csv data/sachs/cd3cd28icam2_g0076.csv \
        data/sachs/cd3cd28icam2_ly.csv data/sachs/cd3cd28icam2_psit.csv data/sachs/cd3cd28icam2_u0126.csv \
        data/sachs/pma.csv \
    -o "$OUTPUT_FILE" \
    -a $val \
    --technique-kwargs random_seed="$seed" population_size=7 num_parents_mating=4 \
    -V PKA Jnk PKC P38 Akt PIP3 Erk Mek Raf PIP2 Plcg

echo "======================================================"
echo "Run for alpha=${val} and random_seed=${seed} completed."