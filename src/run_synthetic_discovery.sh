#!/bin/bash
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

echo "sbatch src/run_synthetic_discovery.sh $@"

apptainer exec apptainer.sif src/synthetic_discovery.py $@

echo "COMPLETED"
