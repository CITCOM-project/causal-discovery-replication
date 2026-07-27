#Used for hc and nsga, pc and pgmhc have their own versions

import argparse
import pandas as pd
import numpy as np
import networkx as nx
import os

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", required=True)
parser.add_argument("-t", "--truth", required=True)
args = parser.parse_args()

os.makedirs("causal_discovery_rp/methods/partials", exist_ok=True)

seeds = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300]
percents = [1, 3, 5, 10, 15, 20, 25, 30, 40, 50]

multi_graph = nx.nx_pydot.read_dot(args.truth)
graph = nx.DiGraph(multi_graph)

edges = list(graph.edges)
edges_set = set(edges)
non_edges = [(i, j) for i in graph.nodes for j in graph.nodes if i != j and (i, j) not in edges_set]

num_edges = len(edges)
num_non_edges = len(non_edges)

for seed in seeds:
    for percent in percents:
        np.random.seed(seed)

        num_to_include = int(num_edges * percent / 100)
        num_to_exclude = int(num_non_edges * percent / 100)

        req_indices = np.random.choice(num_edges, size=num_to_include, replace=False)
        included_edges = [edges[idx] for idx in req_indices]
            
        exc_indices = np.random.choice(num_non_edges, size=num_to_exclude, replace=False)
        excluded_edges = [non_edges[idx] for idx in exc_indices]

        with open(f"causal_discovery_rp/methods/partials/{args.output}_percent_{percent}_seed_{seed}_excluded.dot", "x") as f:
            f.write("digraph {\n")
            for u, v in excluded_edges:
                f.write(f"{u} -> {v};\n")
            f.write("}")
        
        with open(f"causal_discovery_rp/methods/partials/{args.output}_percent_{percent}_seed_{seed}_included.dot", "x") as f:
            f.write("digraph {\n")
            for u, v in included_edges:
                f.write(f"{u} -> {v};\n")
            f.write("}")