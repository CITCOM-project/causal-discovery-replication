import argparse
import pandas as pd
import numpy as np
from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.PCUtils.BackgroundKnowledge import BackgroundKnowledge
from causallearn.utils.GraphUtils import GraphUtils

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--data", nargs='+', required=True) # Mapped to args.data
parser.add_argument("-o", "--output", required=True)
parser.add_argument("-a", "--alpha", type=float, default=0.05)
parser.add_argument("-c", "--context", action="store_true", default=False, required=False)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("-V", "--variables", nargs='*')
args = parser.parse_args()

np.random.seed(args.seed)

# load data
if args.context:
    dfs = []
    for i, path in enumerate(args.data):
        temp_df = pd.read_csv(path)
        temp_df['file_index'] = i
        dfs.append(temp_df)

    df = pd.concat(dfs, ignore_index=True)
    if args.variables:
        df = df[list(set(args.variables + ['file_index']))]

    bk = BackgroundKnowledge().add_forbidden_by_pattern(".*", "file_index")
else:
    df = pd.concat((pd.read_csv(path) for path in args.data), ignore_index=True)
    
    if args.variables:
        df = df[args.variables]

# clean data
df.dropna(inplace=True)

for col in df.select_dtypes(include=['object', 'string']).columns:
    df[col] = df[col].astype('category').cat.codes

# drop columns with zero variance
variance_mask = df.nunique() > 1
if not variance_mask.all():
    dropped_consts = df.columns[~variance_mask].tolist()
    print(f"WARNING: Dropping constant columns (zero variance): {dropped_consts}")
    df = df.loc[:, variance_mask]

# drop perfectly duplicated columns
df_transposed = df.T
duplicate_mask = df_transposed.duplicated()
if duplicate_mask.any():
    dropped_dupes = df.columns[duplicate_mask].tolist()
    print(f"WARNING: Dropping perfectly duplicated columns: {dropped_dupes}")
    df = df.loc[:, ~duplicate_mask]

node_labels = df.columns.tolist()
data = df.to_numpy().astype(float)

# run pc
if args.context:
    cg = pc(data, alpha=args.alpha, node_names=node_labels, background_knowledge=bk)
else:
    cg = pc(data, alpha=args.alpha, node_names=node_labels)

# post processing
if args.context:
    file_node = next((node for node in cg.G.nodes if node.name == "file_index"), None)
    if file_node:
        cg.G.remove_node(file_node)
        node_labels.remove("file_index")

# output
pyd = GraphUtils.to_pydot(cg.G, labels=node_labels)
pyd.write_dot(args.output)