import random

from discovery import techniques

configurations = []
for seed in range(250):
    for technique in techniques:
        random.seed(seed)
        data = random.randint(10, 1000)
        n_nodes = random.randint(10, 30)
        p_conditional = random.random()
        output_file = f"results_synthetic/{technique}/{seed}.dot"
        reference_output_file = f"reference_synthetic/{technique}/{seed}.dot"
        configurations.append(
            f"-t {technique} -D {data} -n {n_nodes} -c {p_conditional} -s {seed} -o {output_file} -r {reference_output_file}"
        )


with open("synthetic_configurations.txt", "w") as f:
    f.write("\n".join(configurations))
