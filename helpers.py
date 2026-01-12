##! this is a helper file gathering usfull functions for the analazys in this project


from pathlib import Path
import pandas as pd


def load_tables(data_dir: str):
    tables = {}

    for p in Path(data_dir).iterdir():
        if p.is_file() and p.suffix == ".csv":
            tables[p.stem] = pd.read_csv(p)

    return tables
