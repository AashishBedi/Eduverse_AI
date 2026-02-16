"""
Query analyzer for timetable queries
Extracts structured parameters from natural language queries
"""

import re
from typing import Optional, Dict, Any
from enum import Enum


class QueryIntent(str, Enum):
    """Query intent types"""
    TEACHER_LOOKUP = "teacher_lookup"
    DAY_LOOKUP = "day_lookup"
    SEMANTIC = "semantic"


class QueryAnalysis:
    """Structured query analysis result"""
    
    def __init__(
        self,
        teacher_id: Optional[str] = None,
        teacher_name: Optional[str] = None,
        day: Optional[str] = None,
        intent: QueryIntent = QueryIntent.SEMANTIC
    ):
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.day = day
        self.intent = intent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "day": self.day,
            "intent": self.intent.value
        }
    
    def __repr__(self):
        return f"QueryAnalysis(teacher_id={self.teacher_id}, day={self.day}, intent={self.intent})"


def analyze_query(query: str) -> QueryAnalysis:
    """
    Analyze timetable query to extract structured parameters
    
    Extracts:
    - Numeric teacher IDs (4-6 digits)
    - Teacher names (patterns with sir, Dr., Prof., etc.)
    - Day names (Monday-Sunday)
    
    Args:
        query: User query string
        
    Returns:
        QueryAnalysis object with extracted parameters and intent
    """
    query_lower = query.lower().strip()
    
    # Extract teacher ID (numeric, 4-6 digits)
    teacher_id = extract_teacher_id(query)
    
    # Extract teacher name
    teacher_name = extract_teacher_name(query)
    
    # Extract day
    day = extract_day(query)
    
    # Determine intent
    if teacher_id or teacher_name:
        intent = QueryIntent.TEACHER_LOOKUP
    elif day:
        intent = QueryIntent.DAY_LOOKUP
    else:
        intent = QueryIntent.SEMANTIC
    
    return QueryAnalysis(
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        day=day,
        intent=intent
    )


def extract_teacher_id(query: str) -> Optional[str]:
    """
    Extract numeric teacher ID from query
    
    Supports:
    - Pure numeric: "11265", "23538"
    - With context: "teacher 11265", "ID 23538", "teacher ID 11265"
    - Prefixed: "T001", "TEACHER001"
    
    Args:
        query: User query
        
    Returns:
        Teacher ID as string (normalized), or None if not found
    """
    # Pattern 1: Pure numeric ID (4-6 digits)
    numeric_pattern = r'\b(\d{4,6})\b'
    match = re.search(numeric_pattern, query)
    if match:
        return match.group(1).strip()  # Normalize
    
    # Pattern 2: Prefixed IDs (T001, TEACHER001)
    prefix_pattern = r'\b(T\d+|TEACHER\d+)\b'
    match = re.search(prefix_pattern, query, re.IGNORECASE)
    if match:
        return match.group(1).upper().strip()  # Normalize
    
    return None


def extract_teacher_name(query: str) -> Optional[str]:
    """
    Extract teacher name from query
    
    Patterns:
    - "manik sir", "anshu sir"
    - "Dr. Anshu", "Prof. Kumar"
    - "Mr. John", "Ms. Smith"
    
    Args:
        query: User query
        
    Returns:
        Teacher name if found, None otherwise
    """
    # Pattern 1: Name + "sir" (common in India)
    sir_pattern = r'\b([a-z]+)\s+sir\b'
    match = re.search(sir_pattern, query, re.IGNORECASE)
    if match:
        return f"{match.group(1)} sir"
    
    # Pattern 2: Title + Name (Dr., Prof., Mr., Ms., Mrs.)
    title_pattern = r'\b(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    match = re.search(title_pattern, query, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    
    return None


def extract_day(query: str) -> Optional[str]:
    """
    Extract day of week from query
    
    Args:
        query: User query
        
    Returns:
        Day name (capitalized) if found, None otherwise
    """
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    query_lower = query.lower()
    
    for day in days:
        if day in query_lower:
            return day.capitalize()
    
    return None
