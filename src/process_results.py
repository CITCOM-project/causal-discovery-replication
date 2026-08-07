import pydot
import pandas as pd
from glob import glob
import os
from itertools import takewhile

data = []
for dag_path in glob("results/**/*.dot", recursive=True):
    split = os.path.normpath(os.path.splitext(dag_path)[0]).split(os.sep)
    system = list(takewhile(lambda directory: not directory.startswith("technique-"), split))
    dag = pydot.graph_from_dot_file(dag_path)[0]
    configuration = dict(map(lambda directory: directory.split("-"), split[len(system) :]))
    configuration = {k: float(v) for k, v in configuration.items() if k != "technique"}
    configuration |= dag.get_attributes()
    data.append(configuration)
data = pd.DataFrame(data)
print(data)
