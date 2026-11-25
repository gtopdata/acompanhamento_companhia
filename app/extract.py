'''imports'''
from pathlib import Path

import pandas as pd



def load_data(path: Path) -> pd.DataFrame:
    '''Busca um arquivo .parquet no path informado'''
    return pd.read_parquet(path)
