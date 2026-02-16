"""
Smart Excel loader with automatic header detection
Handles messy Excel files with inconsistent header positions
"""

import pandas as pd
import io
from typing import Tuple, Optional


def load_excel_smart(file_bytes: bytes, filename: str = "file.xlsx") -> pd.DataFrame:
    """
    Load Excel file with automatic header row detection
    
    Handles cases where:
    - Header is not at row 0
    - There are blank rows before header
    - There is metadata/title rows before actual data
    
    Args:
        file_bytes: Excel file content as bytes
        filename: Original filename (for extension detection)
        
    Returns:
        Clean DataFrame with proper headers
        
    Raises:
        ValueError: If header row cannot be detected
    """
    # Determine file extension
    file_ext = filename.lower().split('.')[-1]
    
    # Read Excel without assuming header position
    try:
        if file_ext == 'csv':
            df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None)
        else:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {str(e)}")
    
    # Detect header row
    header_row = _detect_header_row(df_raw)
    
    if header_row is None:
        raise ValueError(
            "Could not detect header row. Expected columns like 'Monday', 'Tuesday', "
            "or 'teacher_uid', 'subject', 'day', etc."
        )
    
    # Re-read with detected header
    try:
        if file_ext == 'csv':
            df_clean = pd.read_csv(io.BytesIO(file_bytes), header=header_row)
        else:
            df_clean = pd.read_excel(io.BytesIO(file_bytes), header=header_row)
    except Exception as e:
        raise ValueError(f"Failed to re-read Excel with header row {header_row}: {str(e)}")
    
    # Clean column names
    df_clean = _clean_columns(df_clean)
    
    # Remove completely empty rows
    df_clean = df_clean.dropna(how='all')
    
    return df_clean


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean column names and remove problematic columns
    
    - Strip whitespace
    - Lowercase
    - Remove duplicate unnamed columns
    - Drop completely empty columns
    """
    # Create a copy to avoid mutation
    df = df.copy()
    
    # Clean column names
    new_columns = []
    unnamed_count = 0
    
    for col in df.columns:
        col_str = str(col).strip().lower()
        
        # Handle unnamed columns from merged cells
        if col_str.startswith('unnamed'):
            # Check if this column is completely empty
            if df[col].isna().all():
                new_columns.append(f'_drop_{unnamed_count}')
                unnamed_count += 1
            else:
                new_columns.append(col_str)
        else:
            new_columns.append(col_str)
    
    df.columns = new_columns
    
    # Drop columns marked for removal
    df = df[[col for col in df.columns if not col.startswith('_drop_')]]
    
    return df


def _detect_header_row(df: pd.DataFrame, max_rows: int = 15) -> Optional[int]:
    """
    Detect which row contains the header
    
    Priority logic:
    1. Look for row with "time" column AND at least 2 day names (visual format)
    2. Look for row with standard timetable columns (simple format)
    
    Args:
        df: Raw DataFrame (no header)
        max_rows: Maximum number of rows to scan
        
    Returns:
        Row index of header, or None if not found
    """
    # Day names to look for (visual format indicator)
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Standard column names (simple format indicator)
    standard_cols = ['teacher_uid', 'teacher_name', 'subject', 'day', 'start_time', 'end_time', 'classroom']
    
    # Scan first N rows
    for row_idx in range(min(max_rows, len(df))):
        row = df.iloc[row_idx]
        
        # Convert row values to lowercase strings and clean them
        row_values = [str(val).lower().strip() for val in row if pd.notna(val)]
        
        # Priority 1: Check for visual format (time + day names)
        has_time = any('time' in val for val in row_values)
        day_count = sum(1 for val in row_values if any(day in val for day in day_names))
        
        if has_time and day_count >= 2:  # Time column + at least 2 day columns
            return row_idx
        
        # Priority 2: Check for standard columns (simple format)
        standard_count = sum(1 for val in row_values if any(col in val for col in standard_cols))
        if standard_count >= 4:  # At least 4 standard columns
            return row_idx
    
    return None


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename
    
    Args:
        filename: Original filename
        
    Returns:
        Lowercase file extension (e.g., 'xlsx', 'csv')
    """
    return filename.lower().split('.')[-1] if '.' in filename else ''
