xargs -n 1 -a synthetic_configurations.txt -L 1 sbatch --time=04:00:00 --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=8G apptainer exec apptainer.sif python src/synthetic_discovery.py 
