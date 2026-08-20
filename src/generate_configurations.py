import random

from discovery import techniques

DATA_SIZES = [100, 1000, 5000]
PROBABILITIES = [0.25, 0.5, 0.75, 1]
NODES = [10, 20, 30]

configurations = []
for seed in range(250):
    for technique in techniques:
        random.seed(seed)
        data = random.randint(10, 1000)
        nodes = random.randint(10, 30)
        p_edge = random.uniform(0.25, 1)
        p_conditional = random.uniform(0.25, 1)
        output_file = f"results_synthetic/{technique}/{seed}.dot"
        configurations.append(
            f"-o {output_file} -t {technique} -D {data} -n {nodes} -E {p_edge} -c {p_conditional} -s {seed}"
        )


with open("synthetic_configurations.txt", "w") as f:
    f.write("\n".join(configurations))
