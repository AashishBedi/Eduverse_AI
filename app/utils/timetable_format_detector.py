"""
Timetable format detection layer
Determines whether timetable is in simple or visual format
"""

import pandas as pd
from typing import Literal


TimetableFormat = Literal['simple', 'visual']


def detect_timetable_format(df: pd.DataFrame) -> TimetableFormat:
    """
    Detect timetable format type
    
    CRITICAL: Detects visual format FIRST to avoid false simple format validation
    
    Args:
        df: DataFrame with headers (already cleaned)
        
    Returns:
        'simple' - Flat table with required columns
        'visual' - Time-slot rows with day columns
        
    Raises:
        ValueError: If format cannot be determined
    """
    # Get column names (should already be lowercase from cleaning)
    cols_lower = [str(col).lower().strip() for col in df.columns]
    
    # PRIORITY 1: Check for visual format FIRST
    # Visual format indicators:
    # 1. Has a "time" column
    # 2. Has at least 3 day columns
    
    has_time_col = any('time' in col for col in cols_lower)
    
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_cols = [col for col in cols_lower if any(day == col or day in col for day in day_names)]
    
    if has_time_col and len(day_cols) >= 3:
        return 'visual'
    
    # PRIORITY 2: Check for simple format
    # Required columns for simple format
    required_simple = {'teacher_uid', 'teacher_name', 'subject', 'day', 'start_time', 'end_time'}
    
    # Check if it has standard columns (simple format)
    matching_simple = sum(1 for col in cols_lower if any(req in col for req in required_simple))
    
    if matching_simple >= 4:
        return 'simple'
    
    # Cannot determine format
    raise ValueError(
        f"Cannot determine timetable format. "
        f"Found columns: {', '.join(cols_lower)}. "
        f"Expected either:\n"
        f"  - Visual format: 'time' column + day columns (monday, tuesday, etc.)\n"
        f"  - Simple format: teacher_uid, subject, day, start_time, end_time"
    )


def is_simple_format(df: pd.DataFrame) -> bool:
    """
    Check if DataFrame is in simple format
    
    Args:
        df: DataFrame with headers
        
    Returns:
        True if simple format, False otherwise
    """
    try:
        return detect_timetable_format(df) == 'simple'
    except ValueError:
        return False


def is_visual_format(df: pd.DataFrame) -> bool:
    """
    Check if DataFrame is in visual format
    
    Args:
        df: DataFrame with headers
        
    Returns:
        True if visual format, False otherwise
    """
    try:
        return detect_timetable_format(df) == 'visual'
    except ValueError:
        return False
