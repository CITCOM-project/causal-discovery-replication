import argparse
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.preprocessing import StandardScaler
from pgmpy.causal_discovery import HillClimbSearch, ExpertKnowledge

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--data", nargs='+', required=True)
parser.add_argument("-o", "--output", required=True)
parser.add_argument("-c", "--context", action="store_true", default=False)
parser.add_argument("-t", "--truth", required=True)
parser.add_argument("-p", "--percent", type=int, required=True)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("-V", "--variables", nargs='*')
args = parser.parse_args()

np.random.seed(args.seed)

multi_graph = nx.nx_pydot.read_dot(args.truth)
graph = nx.DiGraph(multi_graph)

edges = list(graph.edges)
non_edges = [(i,j) for i in graph.nodes for j in graph.nodes if i != j and (i, j) not in edges]

num_to_include = int(len(edges) * args.percent / 100)
num_to_exclude = int(len(non_edges) * args.percent / 100)

req_indices = np.random.choice(len(edges), size=num_to_include, replace=False)
included_edges = [edges[idx] for idx in req_indices]
    
exc_indices = np.random.choice(len(non_edges), size=num_to_exclude, replace=False)
excluded_edges = [non_edges[idx] for idx in exc_indices]

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

    excluded_edges.extend([(edge, "file_index") for edge in df.columns if edge != "file_index"])
else:
    df = pd.concat((pd.read_csv(path) for path in args.data), ignore_index=True)
    if args.variables:
        df = df[args.variables]

# clean data
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

cat_cols = df.select_dtypes(include=['object', 'string']).columns
for col in cat_cols:
    df[col] = df[col].astype('category').cat.codes

# remove zero-variance columns
variances = df.var()
constant_cols = variances[variances == 0].index
if len(constant_cols) > 0:
    print(f"Warning: Dropping constant columns due to zero variance: {list(constant_cols)}")
    df = df.drop(columns=constant_cols)

# standardize
all_numeric_cols = df.select_dtypes(include=[np.number]).columns
continuous_cols = [col for col in all_numeric_cols if col not in cat_cols and col != 'file_index']

if len(continuous_cols) > 0:
    scaler = StandardScaler()
    df[continuous_cols] = scaler.fit_transform(df[continuous_cols])

# HillClimb
kwargs = {"return_type": "dag"}
kwargs["expert_knowledge"] = ExpertKnowledge(forbidden_edges=excluded_edges, required_edges=included_edges)

estimator = HillClimbSearch(**kwargs)
estimator.fit(df)
graph = estimator.causal_graph_ 

# post-processing removal
if args.context and "file_index" in graph.nodes():
    graph.remove_node("file_index")

# output
pydot_graph = nx.nx_pydot.to_pydot(graph)
pydot_graph.write_dot(args.output)