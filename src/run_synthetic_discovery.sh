echo "sbatch src/run_synthetic_discovery.sh $@"

python src/synthetic_discovery.py $@

echo "COMPLETED"
