import pandas as pd
import numpy as np
import importlib
import inspect

def generate_causal_data(num_samples=1000, func_name=str):
    target_module = importlib.import_module(func_name)
    target_func = getattr(target_module, func_name)
    sig = inspect.signature(target_func)
    x_param_names = [name for name in sig.parameters if name.startswith('X')]
    x_samples_dict = {
        name: np.random.uniform(0.0, 10.0, num_samples) 
        for name in x_param_names
    }
    
    data_rows = []
    
    for i in range(num_samples):
        row_kwargs = {name: x_samples_dict[name][i] for name in x_param_names}
        y_dict = target_func(**row_kwargs)
        
        row = row_kwargs.copy()
        row.update(y_dict)        
        data_rows.append(row)
        
    df = pd.DataFrame(data_rows)    
    
    y_cols = [col for col in df.columns if col.startswith('Y')]
    x_cols_sorted = sorted(x_param_names, key=lambda x: int(x[1:]))
    y_cols_sorted = sorted(y_cols, key=lambda y: int(y[1:]))
    df = df[x_cols_sorted + y_cols_sorted]
    
    return df

if __name__ == "__main__":
    nodes = [10, 20, 30]
    edges = [0.25, 0.5, 0.75, 1]
    samples = [100, 250, 500, 1000, 3000, 5000, 10000, 20000]
    
    for node in nodes:
        for edge in edges:
            function = f"program_node_{node}_edge_{int(edge*100)}"
            for sample in samples:
                dataset = generate_causal_data(num_samples=sample, func_name=function)
                filename = f"data/synth/data/{function}_{sample}_samples.csv"
                dataset.to_csv(filename, index=False)
                print(f"Generated: {filename}")