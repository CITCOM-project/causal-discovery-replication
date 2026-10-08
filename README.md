# Causal Discovery Replication Package

This is the replication package for our paper entitled "CHANGEME".
We make use of several packages from both python and R, which can be tricky to install.
Rather than doing all this locally, we recommend you use [apptainer](https://apptainer.org/) to manage this.

## Setup
The only setup required is to build the apptainer image from the root directory:
```
sudo apptainer build apptainer.sif apptainer.def
```
This will create a file called `apptainer.sif` in the

If you don't want to use apptainer, you will need to set up a virtual environment and install the dependencies from `pyproject.toml` in the usual way.

## RQ1 and 2
To reproduce our experiment for RQ1 on a slurm HPC, run

```
xargs -n 1 -a synthetic_configurations.txt -L 1 sbatch --time=04:00:00 --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=8G apptainer exec apptainer.sif python src/synthetic_discovery.py
```

to run this locally, run

```
xargs -n 1 -a synthetic_configurations.txt -L 1 apptainer exec apptainer.sif python src/synthetic_discovery.py
```

optionally, if you have multiple cores, you can use the `-P $cores` argument to xargs to speed things up a bit.

This will produce a directory called `results_synthetic` with subdirectories for each technique.
Each subdirectory will contain 250 inferred DAG files with the experimental configuration recorded as attributes.
To generate the figures in the paper, run `python src/process_results.py`
This will generate a `figures` directory with all the figures in, and a `stats` directory with the outputs from the various statistical tests.

## RQ3
TODO
