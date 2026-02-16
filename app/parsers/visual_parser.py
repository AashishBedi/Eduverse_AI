"""
Visual timetable parser
Handles grid format with time slots in rows and days in columns
"""

import pandas as pd
import re
from typing import List, Tuple, Dict, Optional
from datetime import datetime, time as dt_time


def parse_time_range(time_value) -> Optional[Tuple[str, str]]:
    """
    Parse time range from various formats into (start_time, end_time) as HH:MM strings
    
    Handles:
    - "09:00-10:00"
    - "09:00 – 10:00" (en dash)
    - "9:00 AM - 10:00 AM"
    - "9:00AM-10:00AM"
    - "09.00-10.00"
    - Excel datetime objects
    
    Returns:
        Tuple of (start_time, end_time) in "HH:MM" format, or None if invalid
    """
    # Handle None/NaN
    if pd.isna(time_value):
        return None
    
    # Convert to string safely
    time_str = str(time_value).strip()
    
    # Handle empty strings
    if not time_str or time_str.lower() == 'nan':
        return None
    
    # Clean the string
    # Replace en dash, em dash with regular dash
    time_str = time_str.replace('–', '-').replace('—', '-')
    # Replace dots with colons
    time_str = time_str.replace('.', ':')
    # Remove extra spaces
    time_str = ' '.join(time_str.split())
    
    # Flexible regex to extract two times
    # Matches: "9:00 AM", "09:00", "900", etc.
    pattern = re.compile(
        r'(\d{1,2}):?(\d{2})?\s*(AM|PM|am|pm)?\s*[-to]*\s*(\d{1,2}):?(\d{2})?\s*(AM|PM|am|pm)?',
        re.IGNORECASE
    )
    
    match = pattern.search(time_str)
    if not match:
        return None
    
    try:
        # Parse start time
        start_hour = int(match.group(1))
        start_min = int(match.group(2)) if match.group(2) else 0
        start_period = match.group(3).upper() if match.group(3) else None
        
        # Parse end time
        end_hour = int(match.group(4))
        end_min = int(match.group(5)) if match.group(5) else 0
        end_period = match.group(6).upper() if match.group(6) else None
        
        # Convert to 24-hour format
        if start_period == 'PM' and start_hour != 12:
            start_hour += 12
        elif start_period == 'AM' and start_hour == 12:
            start_hour = 0
        
        if end_period == 'PM' and end_hour != 12:
            end_hour += 12
        elif end_period == 'AM' and end_hour == 12:
            end_hour = 0
        
        # Validate hours and minutes
        if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
            return None
        if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
            return None
        
        # Format as HH:MM
        start_time = f"{start_hour:02d}:{start_min:02d}"
        end_time = f"{end_hour:02d}:{end_min:02d}"
        
        return (start_time, end_time)
        
    except (ValueError, AttributeError, IndexError):
        return None


def parse_visual_timetable(
    df: pd.DataFrame,
    department: str,
    academic_year: str
) -> List[Tuple]:
    """
    Parse visual timetable format (time slots in rows, days in columns)
    
    Robust parsing with:
    - Flexible time regex
    - Defensive cell cleaning
    - Dynamic column detection
    - Adjacent classroom column support
    - Debug logging
    
    Args:
        df: DataFrame with visual format (already cleaned columns)
        department: Department name
        academic_year: Academic year
        
    Returns:
        List of tuples ready for DB insert:
        (teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Create a copy to avoid mutating original
    df = df.copy()
    
    # Extract teacher info from entire DataFrame (checks first 5 rows)
    teacher_info = _extract_teacher_info(df)
    logger.info(f"Extracted teacher info: {teacher_info}")
    
    # Identify time column (look for column with "time" in name)
    time_col = None
    for col in df.columns:
        if 'time' in str(col).lower():
            time_col = col
            break
    
    if not time_col:
        # Fallback: use first column
        time_col = df.columns[0]
    
    logger.info(f"Time column: {time_col}")
    
    # Identify day columns with their indices
    day_columns = _identify_day_columns_with_adjacent(df.columns)
    
    if not day_columns:
        raise ValueError(
            f"No day columns found. Expected columns like monday, tuesday, etc. "
            f"Found columns: {', '.join(df.columns)}"
        )
    
    logger.info(f"Day columns found: {day_columns}")
    
    # Find where actual timetable data starts (rows with time patterns)
    start_row = _find_timetable_start_row(df, time_col)
    logger.info(f"Timetable starts at row: {start_row}")
    
    # Extract timetable data
    timetable_df = df.iloc[start_row:].copy().reset_index(drop=True)
    
    # Parse entries with debug info
    entries = []
    cells_inspected = 0
    rows_with_time = 0
    rows_skipped_no_time = 0
    
    for row_idx, row in timetable_df.iterrows():
        time_slot_raw = row[time_col]
        
        # Parse time range using flexible parser
        time_result = parse_time_range(time_slot_raw)
        
        if not time_result:
            rows_skipped_no_time += 1
            # Log first few failures for debugging
            if rows_skipped_no_time <= 3:
                logger.warning(f"Row {row_idx}: Could not parse time from: {time_slot_raw}")
            continue
        
        rows_with_time += 1
        start_time, end_time = time_result
        
        # Parse each day column
        for day_info in day_columns:
            day = day_info['day']
            subject_col_idx = day_info['subject_idx']
            classroom_col_idx = day_info.get('classroom_idx')
            
            cells_inspected += 1
            
            # Get subject cell value
            subject_cell_raw = row.iloc[subject_col_idx]
            
            # Defensive cleaning
            if pd.isna(subject_cell_raw):
                continue
            
            subject_cell = str(subject_cell_raw).replace('\n', ' ').strip()
            
            # Skip truly empty cells
            if not subject_cell or subject_cell.lower() in ['nan', '-', 'n/a', 'none', '']:
                continue
            
            # Parse subject
            subject = _parse_subject(subject_cell)
            
            # Get classroom from adjacent column if available
            classroom = 'TBA'
            if classroom_col_idx is not None and classroom_col_idx < len(row):
                classroom_cell_raw = row.iloc[classroom_col_idx]
                if not pd.isna(classroom_cell_raw):
                    classroom_cell = str(classroom_cell_raw).replace('\n', ' ').strip()
                    if classroom_cell and classroom_cell.lower() not in ['nan', '-', 'n/a', 'none', '']:
                        classroom = classroom_cell
            
            if subject:
                entry = (
                    teacher_info['uid'],
                    teacher_info['name'],
                    subject,
                    day,
                    start_time,
                    end_time,
                    classroom,
                    department
                )
                entries.append(entry)
    
    # Log debug info
    logger.info(f"Parsing summary:")
    logger.info(f"  - Total rows processed: {len(timetable_df)}")
    logger.info(f"  - Rows with valid time: {rows_with_time}")
    logger.info(f"  - Rows skipped (no valid time): {rows_skipped_no_time}")
    logger.info(f"  - Cells inspected: {cells_inspected}")
    logger.info(f"  - Entries created: {len(entries)}")
    
    # Log first 5 entries for debugging
    if entries:
        logger.info(f"First {min(5, len(entries))} entries:")
        for i, entry in enumerate(entries[:5]):
            logger.info(f"  {i+1}. {entry}")
    
    if not entries:
        raise ValueError(
            f"No valid entries found in the visual timetable. "
            f"Processed {len(timetable_df)} rows, found {rows_with_time} with valid time, "
            f"inspected {cells_inspected} cells. "
            f"Day columns: {[d['day'] for d in day_columns]}. "
            f"Check if cells contain actual subject data."
        )
    
    return entries


def _extract_teacher_info(df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract teacher information from header rows or first cell
    
    Looks for patterns like:
    - "23500: Dr. Anshu Vashisth"
    - "23538 manik sir"
    - "Faculty: Dr. John Doe"
    - "T001: John Doe"
    """
    import logging
    logger = logging.getLogger(__name__)
    
    teacher_info = {
        'uid': 'UNKNOWN',
        'name': 'TBA'
    }
    
    # Search first 5 rows for teacher information
    for idx in range(min(5, len(df))):
        for col in df.columns:
            cell_value = str(df.iloc[idx][col]).strip()
            
            # Skip empty cells
            if not cell_value or cell_value.lower() == 'nan':
                continue
            
            logger.info(f"Checking cell [{idx},{col}]: '{cell_value}'")
            
            # Pattern 1: "23500: Dr. Anshu Vashisth" or "T001: John Doe"
            match = re.search(r'([A-Z]?\d{3,6}):\s*(.+?)(?:\s{2,}|$)', cell_value, re.IGNORECASE)
            if match:
                teacher_info['uid'] = match.group(1).strip()
                teacher_info['name'] = match.group(2).strip()
                logger.info(f"✅ Pattern 1 matched: UID={teacher_info['uid']}, Name={teacher_info['name']}")
                return teacher_info
            
            # Pattern 2: "23538 manik sir" (number followed by name)
            match = re.search(r'^(\d{4,6})\s+([a-zA-Z\s]+)$', cell_value, re.IGNORECASE)
            if match:
                teacher_info['uid'] = match.group(1).strip()
                teacher_info['name'] = match.group(2).strip()
                logger.info(f"✅ Pattern 2 matched: UID={teacher_info['uid']}, Name={teacher_info['name']}")
                return teacher_info
            
            # Pattern 3: Just a number (4-6 digits) in first cell
            match = re.search(r'^\s*(\d{4,6})\s*$', cell_value)
            if match:
                teacher_info['uid'] = match.group(1).strip()
                logger.info(f"✅ Pattern 3 matched (UID only): UID={teacher_info['uid']}")
                return teacher_info
            
            # Pattern 4: Number anywhere in the cell
            match = re.search(r'\b(\d{4,6})\b', cell_value)
            if match and idx == 0:  # Only in first row
                teacher_info['uid'] = match.group(1).strip()
                # Try to extract name from rest of cell
                name_part = cell_value.replace(match.group(1), '').strip()
                if name_part and len(name_part) > 2:
                    teacher_info['name'] = name_part
                logger.info(f"✅ Pattern 4 matched: UID={teacher_info['uid']}, Name={teacher_info['name']}")
                return teacher_info
    
    logger.warning(f"⚠️ Could not extract teacher info, using defaults: {teacher_info}")
    return teacher_info


def _find_timetable_start_row(df: pd.DataFrame, time_col: str = None) -> int:
    """
    Find the row where actual timetable data starts
    (after header/metadata rows)
    
    Args:
        df: DataFrame
        time_col: Name of time column (optional)
    """
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    
    # If time_col specified, check that column
    if time_col:
        for idx in range(min(15, len(df))):
            row_val = str(df.iloc[idx][time_col]).lower()
            if time_pattern.search(row_val):
                return idx
    else:
        # Check first column
        for idx in range(min(15, len(df))):
            row_str = str(df.iloc[idx, 0]).lower()
            if time_pattern.search(row_str):
                return idx
    
    return 0


def _identify_day_columns(columns: pd.Index) -> Dict[int, str]:
    """
    Identify which columns contain day names
    
    Returns:
        Dictionary mapping column index to day name (capitalized)
    """
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    day_columns = {}
    
    for idx, col in enumerate(columns[1:], start=1):  # Skip first column (time)
        col_lower = str(col).lower()
        for day in days_of_week:
            if day in col_lower:
                day_columns[idx] = day.capitalize()
                break
    
    return day_columns


def _identify_day_columns_with_adjacent(columns: pd.Index) -> List[Dict]:
    """
    Identify day columns and their adjacent columns (for classroom info)
    
    Returns:
        List of dictionaries with:
        - day: Day name (capitalized)
        - subject_idx: Column index for subject
        - classroom_idx: Column index for classroom (if adjacent unnamed column exists)
    """
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    day_columns = []
    
    for idx, col in enumerate(columns[1:], start=1):  # Skip first column (time)
        col_lower = str(col).lower()
        
        for day in days_of_week:
            if day in col_lower:
                day_info = {
                    'day': day.capitalize(),
                    'subject_idx': idx,
                    'classroom_idx': None
                }
                
                # Check if next column is unnamed (potential classroom column)
                if idx + 1 < len(columns):
                    next_col = str(columns[idx + 1]).lower()
                    if 'unnamed' in next_col or next_col.strip() == '':
                        day_info['classroom_idx'] = idx + 1
                
                day_columns.append(day_info)
                break
    
    return day_columns


def _parse_subject(cell_value: str) -> Optional[str]:
    """
    Parse subject from cell value
    
    Handles formats like:
    - "C-CSE-23500" → "CSE-23500"
    - "S-CHEMISTRY" → "CHEMISTRY"
    - "Lecture-CS-01" → "CS-01"
    - "Data Structures" → "Data Structures"
    """
    # Clean the value
    cell_value = cell_value.strip()
    
    # Extract subject from format like "C-CSE-23500" or "S-CHEMISTRY"
    if '-' in cell_value:
        parts = cell_value.split('-', 1)
        if len(parts) >= 2:
            return parts[1].strip()
    
    # Return as-is if no special format
    return cell_value


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
