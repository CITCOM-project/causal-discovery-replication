#!/bin/bash
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

echo "sbatch src/run_synthetic_discovery.sh $@"

module load Anaconda3/2024.02-1
source activate causal-discovery

python src/synthetic_discovery.py $@

echo "COMPLETED"
