import pandas as pd
from .state import get_dataset

def load_df() -> pd.DataFrame:
    return get_dataset()  # placeholder; swap to SQLite later if needed
