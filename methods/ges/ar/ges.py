import argparse
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.preprocessing import StandardScaler
from pgmpy.causal_discovery import GES

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--data", nargs='+', required=True)
parser.add_argument("-o", "--output", required=True)
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
else:
    df = pd.concat((pd.read_csv(path) for path in args.data), ignore_index=True)
    if args.variables:
        df = df[args.variables]

# clean data
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

# encode categoricals
cat_cols = df.select_dtypes(include=['object', 'string']).columns
for col in cat_cols:
    df[col] = df[col].astype('category').cat.codes

# remove zero-variance columns
variances = df.var()
constant_cols = variances[variances == 0].index
if len(constant_cols) > 0:
    print(f"Warning: Dropping constant columns due to zero variance: {list(constant_cols)}")
    df = df.drop(columns=constant_cols)

# standardize only originally numerical data
all_numeric_cols = df.select_dtypes(include=[np.number]).columns
continuous_cols = [col for col in all_numeric_cols if col not in cat_cols and col != 'file_index']

if len(continuous_cols) > 0:
    scaler = StandardScaler()
    df[continuous_cols] = scaler.fit_transform(df[continuous_cols])

# run
estimator = GES(return_type="dag")
estimator.fit(df)
graph = estimator.causal_graph_

# post-processing
if args.context and "file_index" in graph.nodes():
    graph.remove_node("file_index")

# output
pydot_graph = nx.nx_pydot.to_pydot(graph)
pydot_graph.write_dot(args.output)