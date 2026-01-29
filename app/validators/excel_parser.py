"""Excel parsing utilities."""
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path


def parse_excel_file(file_path: Path) -> pd.DataFrame:
    """Parse Excel file and return DataFrame."""
    df = pd.read_excel(file_path, sheet_name=0)
    # Remove completely empty rows
    df = df.dropna(how='all').reset_index(drop=True)
    return df


def get_column_names(df: pd.DataFrame) -> List[str]:
    """Get column names from DataFrame."""
    return df.columns.tolist()


def get_sample_data(df: pd.DataFrame, num_rows: int = 5) -> List[Dict[str, Any]]:
    """Get sample data from DataFrame."""
    return df.head(num_rows).to_dict('records')
