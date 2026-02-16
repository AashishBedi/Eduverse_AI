"""
Production-ready multi-format timetable parser
Handles simple flat tables and visual timetable layouts
"""

import pandas as pd
import re
from typing import List, Dict, Any, Tuple, Optional


# ============================================================================
# FORMAT DETECTION
# ============================================================================

def detect_timetable_format(df: pd.DataFrame) -> str:
    """
    Detect timetable format type
    
    Args:
        df: Input DataFrame
        
    Returns:
        'simple' - Flat table with required columns
        'visual' - Time-slot rows with day columns
        
    Raises:
        ValueError: If format cannot be determined
    """
    # Normalize column names for checking
    cols_lower = [str(col).lower().strip().replace(' ', '_') for col in df.columns]
    
    # Required columns for simple format
    required_simple = {'teacher_uid', 'teacher_name', 'subject', 'day', 'start_time', 'end_time'}
    
    # Check if it has standard columns (simple format)
    has_required = len(required_simple.intersection(set(cols_lower))) >= 4
    
    if has_required:
        return 'simple'
    
    # Check for visual format indicators
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_cols = [col for col in cols_lower if any(day in col for day in days_of_week)]
    
    # Check if first column contains time information
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    first_col_has_time = False
    
    if len(df) > 0:
        first_col_values = df.iloc[:, 0].astype(str)
        first_col_has_time = any(time_pattern.search(str(val)) for val in first_col_values[:10])
    
    if len(day_cols) >= 3 and first_col_has_time:
        return 'visual'
    
    # Cannot determine format
    raise ValueError(
        f"Cannot determine timetable format. "
        f"Found columns: {', '.join(cols_lower)}. "
        f"Expected either standard columns (teacher_uid, subject, day, etc.) "
        f"or visual format (time column + day columns)."
    )


# ============================================================================
# SIMPLE FORMAT PARSER
# ============================================================================

def parse_simple_timetable(
    df: pd.DataFrame,
    department: str,
    academic_year: str
) -> List[Dict[str, Any]]:
    """
    Parse simple flat table format
    
    Args:
        df: DataFrame with simple format
        department: Department name
        academic_year: Academic year
        
    Returns:
        List of timetable entry dictionaries
        
    Raises:
        ValueError: If required columns are missing
    """
    # Normalize column names
    df = df.copy()
    df.columns = [str(col).lower().strip().replace(' ', '_') for col in df.columns]
    
    # Required columns
    required = ['teacher_uid', 'teacher_name', 'subject', 'day', 'start_time', 'end_time']
    missing = set(required) - set(df.columns)
    
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    
    # Parse rows
    entries = []
    for _, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['teacher_uid']) or pd.isna(row['subject']):
            continue
        
        entry = {
            'teacher_uid': str(row['teacher_uid']).strip().upper(),
            'teacher_name': str(row['teacher_name']).strip(),
            'subject': str(row['subject']).strip(),
            'day': str(row['day']).strip().capitalize(),
            'start_time': _normalize_time(str(row['start_time'])),
            'end_time': _normalize_time(str(row['end_time'])),
            'classroom': str(row.get('classroom', 'TBA')).strip() if 'classroom' in df.columns else 'TBA',
            'department': str(row.get('department', department)).strip() if 'department' in df.columns else department,
            'academic_year': academic_year
        }
        entries.append(entry)
    
    return entries


# ============================================================================
# VISUAL FORMAT PARSER
# ============================================================================

def parse_visual_timetable(
    df: pd.DataFrame,
    department: str,
    academic_year: str
) -> List[Dict[str, Any]]:
    """
    Parse visual timetable format (time slots in rows, days in columns)
    
    Args:
        df: DataFrame with visual format
        department: Department name
        academic_year: Academic year
        
    Returns:
        List of timetable entry dictionaries
    """
    # Extract teacher info from header
    teacher_info = _extract_teacher_info(df)
    
    # Find the row where actual timetable starts
    start_row = _find_timetable_start_row(df)
    
    # Extract timetable data (skip header rows)
    timetable_df = df.iloc[start_row:].copy().reset_index(drop=True)
    
    # Normalize column names
    timetable_df.columns = [str(col).lower().strip() for col in timetable_df.columns]
    
    # Identify time column (first column)
    time_col = timetable_df.columns[0]
    
    # Identify day columns
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    day_columns = {}
    
    for idx, col in enumerate(timetable_df.columns[1:], start=1):
        for day in days_of_week:
            if day in col:
                day_columns[idx] = day.capitalize()
                break
    
    # Parse entries
    entries = []
    time_pattern = re.compile(r'(\d{1,2}:\d{2})\s*(?:AM|PM|am|pm)?')
    
    for _, row in timetable_df.iterrows():
        time_slot = str(row[time_col]).strip()
        
        # Extract time range
        times = time_pattern.findall(time_slot)
        if len(times) < 2:
            continue
        
        start_time = _normalize_time(times[0])
        end_time = _normalize_time(times[1])
        
        # Parse each day column
        for col_idx, day in day_columns.items():
            cell_value = str(row.iloc[col_idx]).strip()
            
            # Skip empty cells
            if pd.isna(row.iloc[col_idx]) or cell_value == '' or cell_value.lower() in ['nan', '-', 'n/a']:
                continue
            
            # Parse cell content
            subject, classroom = _parse_cell_content(cell_value)
            
            if subject:
                entry = {
                    'teacher_uid': teacher_info['uid'],
                    'teacher_name': teacher_info['name'],
                    'subject': subject,
                    'day': day,
                    'start_time': start_time,
                    'end_time': end_time,
                    'classroom': classroom or 'TBA',
                    'department': department,
                    'academic_year': academic_year
                }
                entries.append(entry)
    
    return entries


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_teacher_info(df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract teacher information from header rows
    
    Looks for patterns like:
    - "23500: Dr. Anshu Vashisth"
    - "Faculty: Dr. John Doe"
    - "Teacher ID: T001"
    """
    teacher_info = {
        'uid': 'UNKNOWN',
        'name': 'TBA'
    }
    
    # Search first 5 rows for teacher information
    for idx in range(min(5, len(df))):
        for col in df.columns:
            cell_value = str(df.iloc[idx][col])
            
            # Pattern: "23500: Dr. Anshu Vashisth" or "T001: John Doe"
            match = re.search(r'([A-Z]?\d{3,6}):\s*(.+?)(?:\s{2,}|$)', cell_value, re.IGNORECASE)
            if match:
                teacher_info['uid'] = match.group(1).upper()
                teacher_info['name'] = match.group(2).strip()
                return teacher_info
            
            # Pattern: "Dr. Name" or "Prof. Name"
            match = re.search(r'((?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+[A-Za-z\s]+)', cell_value)
            if match:
                teacher_info['name'] = match.group(1).strip()
    
    return teacher_info


def _find_timetable_start_row(df: pd.DataFrame) -> int:
    """
    Find the row where actual timetable data starts
    (after header/metadata rows)
    """
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    
    for idx in range(min(15, len(df))):
        row_str = str(df.iloc[idx, 0]).lower()
        if time_pattern.search(row_str):
            return idx
    
    return 0


def _parse_cell_content(cell_value: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse cell content to extract subject and classroom
    
    Formats supported:
    - "C-CSE-23500" → subject: "CSE-23500"
    - "S-CHEMISTRY" → subject: "CHEMISTRY"
    - "Lecture-CS-01\nRoom 101" → subject: "CS-01", classroom: "Room 101"
    
    Returns:
        Tuple of (subject, classroom)
    """
    # Split by newlines
    lines = [line.strip() for line in cell_value.split('\n') if line.strip()]
    
    subject = None
    classroom = None
    
    for line in lines:
        # Extract subject from format like "C-CSE-23500" or "S-CHEMISTRY"
        if '-' in line and not subject:
            parts = line.split('-', 1)
            if len(parts) >= 2:
                subject = parts[1].strip()
        
        # Extract classroom
        room_match = re.search(r'(?:Room|Lab|Hall)\s*(\d+)', line, re.IGNORECASE)
        if room_match:
            classroom = room_match.group(0)
    
    # If no subject found, use entire first line
    if not subject and lines:
        subject = lines[0]
    
    return subject, classroom


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
