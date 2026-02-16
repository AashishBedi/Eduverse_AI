"""
Simple timetable parser
Handles flat table format with standard columns
"""

import pandas as pd
import re
from typing import List, Tuple, Dict, Any


def parse_simple_timetable(
    df: pd.DataFrame,
    department: str,
    academic_year: str
) -> List[Tuple]:
    """
    Parse simple flat table format
    
    Expected columns:
    - teacher_uid
    - teacher_name
    - subject
    - day
    - start_time
    - end_time
    - classroom (optional)
    - department (optional)
    
    Args:
        df: DataFrame with simple format
        department: Department name
        academic_year: Academic year
        
    Returns:
        List of tuples ready for DB insert:
        (teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department)
        
    Raises:
        ValueError: If required columns are missing
    """
    # Create a copy to avoid mutating original
    df = df.copy()
    
    # Normalize column names
    df.columns = [_normalize_column_name(col) for col in df.columns]
    
    # Required columns
    required = ['teacher_uid', 'teacher_name', 'subject', 'day', 'start_time', 'end_time']
    missing = set(required) - set(df.columns)
    
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            f"Found columns: {', '.join(df.columns)}"
        )
    
    # Parse rows
    entries = []
    
    for idx, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['teacher_uid']) or pd.isna(row['subject']):
            continue
        
        # Extract and normalize data
        teacher_uid = str(row['teacher_uid']).strip().upper()
        teacher_name = str(row['teacher_name']).strip()
        subject = str(row['subject']).strip()
        day = str(row['day']).strip().capitalize()
        start_time = _normalize_time(str(row['start_time']))
        end_time = _normalize_time(str(row['end_time']))
        classroom = str(row.get('classroom', 'TBA')).strip() if 'classroom' in df.columns else 'TBA'
        dept = str(row.get('department', department)).strip() if 'department' in df.columns else department
        
        # Create tuple
        entry = (
            teacher_uid,
            teacher_name,
            subject,
            day,
            start_time,
            end_time,
            classroom,
            dept
        )
        entries.append(entry)
    
    if not entries:
        raise ValueError("No valid entries found in the timetable")
    
    return entries


def _normalize_column_name(col: str) -> str:
    """Normalize column name to lowercase with underscores"""
    return str(col).lower().strip().replace(' ', '_').replace('-', '_')


def _normalize_time(time_str: str) -> str:
    """
    Normalize time string to HH:MM format (24-hour)
    
    Examples:
        '11:12 AM' → '11:12'
        '02:20 PM' → '14:20'
        '12:00 PM' → '12:00'
        '12:00 AM' → '00:00'
        '9:00' → '09:00'
    """
    time_str = str(time_str).strip()
    
    # Extract time and AM/PM
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', time_str)
    if not match:
        # Try to handle simple HH:MM format
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                try:
                    hour = int(parts[0])
                    minute = parts[1][:2]
                    return f"{hour:02d}:{minute}"
                except:
                    pass
        return time_str
    
    hour = int(match.group(1))
    minute = match.group(2)
    period = match.group(3)
    
    # Convert to 24-hour format
    if period:
        period_upper = period.upper()
        if period_upper == 'PM' and hour != 12:
            hour += 12
        elif period_upper == 'AM' and hour == 12:
            hour = 0
    
    return f"{hour:02d}:{minute}"
