"""
Timetable service
Deterministic timetable retrieval without LLM
Uses direct database queries for hallucination-free responses
"""

import re
from typing import List, Dict, Any, Optional
from datetime import time
from sqlalchemy.orm import Session
from app.models.timetable import Timetable
from app.db.database import SessionLocal


class TimetableService:
    """
    Service for retrieving timetable information
    Completely deterministic - no LLM involved
    """
    
    # Valid days of the week
    VALID_DAYS = [
        "monday", "tuesday", "wednesday", "thursday", 
        "friday", "saturday", "sunday"
    ]
    
    def __init__(self):
        pass
    
    def extract_teacher_uid(self, text: str) -> Optional[str]:
        """
        Extract teacher UID from text using regex
        
        Supports formats:
        - Numeric: 11265, 23538, 18818 (4-6 digits)
        - Prefixed: T001, T123, TEACHER001
        
        Args:
            text: Input text
            
        Returns:
            Teacher UID if found, None otherwise
        """
        # Pattern 1: Pure numeric ID (4-6 digits)
        numeric_pattern = r'\b(\d{4,6})\b'
        match = re.search(numeric_pattern, text)
        if match:
            return match.group(1)
        
        # Pattern 2: Prefixed IDs (T001, TEACHER001)
        prefix_pattern = r'\b(T\d+|TEACHER\d+)\b'
        match = re.search(prefix_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def extract_day(self, text: str) -> Optional[str]:
        """
        Extract day of week from text
        
        Args:
            text: Input text
            
        Returns:
            Day name (lowercase) if found, None otherwise
        """
        text_lower = text.lower()
        
        for day in self.VALID_DAYS:
            if day in text_lower:
                return day.capitalize()  # Return with first letter capitalized
        
        return None
    
    def get_timetable_by_teacher(
        self, 
        teacher_uid: str, 
        day: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timetable entries for a teacher
        
        Args:
            teacher_uid: Teacher unique ID
            day: Optional day filter
            db: Database session (created if not provided)
            
        Returns:
            List of timetable entries
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            # Normalize teacher_uid (strip whitespace, ensure string)
            teacher_uid = str(teacher_uid).strip()
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Querying timetable for teacher_uid: '{teacher_uid}' (type: {type(teacher_uid).__name__})")
            
            query = db.query(Timetable).filter(
                Timetable.teacher_uid == teacher_uid
            )
            
            if day:
                query = query.filter(Timetable.day == day)
            
            # Order by day and start time
            results = query.order_by(Timetable.day, Timetable.start_time).all()
            
            # Debug logging
            logger.info(f"Query returned {len(results)} results")
            if len(results) == 0:
                # Check if ANY timetable entries exist
                total_count = db.query(Timetable).count()
                logger.warning(f"No results for teacher_uid '{teacher_uid}', but database has {total_count} total entries")
                # Sample some teacher_uid values from database
                sample_uids = db.query(Timetable.teacher_uid).distinct().limit(5).all()
                logger.warning(f"Sample teacher_uid values in database: {[uid[0] for uid in sample_uids]}")
            
            # Convert to dict
            timetable_entries = []
            for entry in results:
                timetable_entries.append({
                    "id": entry.id,
                    "teacher_uid": entry.teacher_uid,
                    "teacher_name": entry.teacher_name,
                    "subject": entry.subject,
                    "day": entry.day,
                    "start_time": entry.start_time.strftime("%H:%M") if entry.start_time else None,
                    "end_time": entry.end_time.strftime("%H:%M") if entry.end_time else None,
                    "classroom": entry.classroom,
                    "department": entry.department
                })
            
            return timetable_entries
            
        finally:
            if should_close:
                db.close()
    
    def get_timetable_by_day(
        self, 
        day: str,
        department: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all timetable entries for a specific day
        
        Args:
            day: Day of week
            department: Optional department filter
            db: Database session
            
        Returns:
            List of timetable entries
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            query = db.query(Timetable).filter(Timetable.day == day)
            
            if department:
                query = query.filter(Timetable.department == department)
            
            results = query.order_by(Timetable.start_time).all()
            
            timetable_entries = []
            for entry in results:
                timetable_entries.append({
                    "id": entry.id,
                    "teacher_uid": entry.teacher_uid,
                    "teacher_name": entry.teacher_name,
                    "subject": entry.subject,
                    "day": entry.day,
                    "start_time": entry.start_time.strftime("%H:%M") if entry.start_time else None,
                    "end_time": entry.end_time.strftime("%H:%M") if entry.end_time else None,
                    "classroom": entry.classroom,
                    "department": entry.department
                })
            
            return timetable_entries
            
        finally:
            if should_close:
                db.close()
    
    def query_timetable(
        self, 
        user_input: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Parse user input and retrieve timetable
        Completely deterministic - no LLM involved
        
        Args:
            user_input: Natural language query
            db: Database session
            
        Returns:
            Dict with timetable data and metadata
        """
        # Extract teacher UID and day
        teacher_uid = self.extract_teacher_uid(user_input)
        day = self.extract_day(user_input)
        
        # Determine query type
        if teacher_uid and day:
            query_type = "teacher_and_day"
            entries = self.get_timetable_by_teacher(teacher_uid, day, db)
        elif teacher_uid:
            query_type = "teacher_only"
            entries = self.get_timetable_by_teacher(teacher_uid, None, db)
        elif day:
            query_type = "day_only"
            entries = self.get_timetable_by_day(day, None, db)
        else:
            query_type = "no_match"
            entries = []
        
        return {
            "query_type": query_type,
            "teacher_uid": teacher_uid,
            "day": day,
            "entries": entries,
            "count": len(entries)
        }
    
    def format_timetable_text(self, timetable_data: Dict[str, Any]) -> str:
        """
        Format timetable data into readable text
        
        Args:
            timetable_data: Output from query_timetable()
            
        Returns:
            Formatted text string
        """
        entries = timetable_data["entries"]
        count = timetable_data["count"]
        teacher_uid = timetable_data["teacher_uid"]
        day = timetable_data["day"]
        
        if count == 0:
            if teacher_uid and day:
                return f"No timetable entries found for teacher {teacher_uid} on {day}."
            elif teacher_uid:
                return f"No timetable entries found for teacher {teacher_uid}."
            elif day:
                return f"No timetable entries found for {day}."
            else:
                # Don't block - suggest semantic search will be used
                return None  # Signal to use semantic search fallback
        
        # Build formatted output
        lines = []
        
        if teacher_uid and day:
            lines.append(f"Timetable for {entries[0]['teacher_name']} ({teacher_uid}) on {day}:")
        elif teacher_uid:
            lines.append(f"Timetable for {entries[0]['teacher_name']} ({teacher_uid}):")
        elif day:
            lines.append(f"Timetable for {day}:")
        
        lines.append("")
        
        # Group by day if showing multiple days
        if not day and teacher_uid:
            current_day = None
            for entry in entries:
                if entry["day"] != current_day:
                    current_day = entry["day"]
                    lines.append(f"\n{current_day}:")
                
                lines.append(
                    f"  • {entry['start_time']} - {entry['end_time']}: "
                    f"{entry['subject']} in {entry['classroom']}"
                )
        else:
            # Single day or day-based query
            for entry in entries:
                lines.append(
                    f"• {entry['start_time']} - {entry['end_time']}: "
                    f"{entry['subject']} - {entry['teacher_name']} ({entry['teacher_uid']}) "
                    f"in {entry['classroom']}"
                )
        
        return "\n".join(lines)


# Global service instance
timetable_service = TimetableService()
