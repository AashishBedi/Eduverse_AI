"""
Timetable endpoints
Deterministic timetable retrieval without LLM
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.timetable_service import timetable_service
from app.db.database import get_db

router = APIRouter()


class TimetableQueryRequest(BaseModel):
    """Timetable query request schema"""
    query: str


class TimetableEntry(BaseModel):
    """Timetable entry schema"""
    id: int
    teacher_uid: str
    teacher_name: str
    subject: str
    day: str
    start_time: str
    end_time: str
    classroom: str
    department: str


class TimetableQueryResponse(BaseModel):
    """Timetable query response schema"""
    query_type: str
    teacher_uid: Optional[str]
    day: Optional[str]
    entries: List[Dict[str, Any]]
    count: int
    formatted_text: str


@router.post("/query", response_model=TimetableQueryResponse)
async def query_timetable(
    request: TimetableQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query timetable using natural language input
    
    This endpoint is completely deterministic and uses direct database queries.
    No LLM is involved - parsing is done with regex.
    
    Examples:
    - "Show me timetable for T001"
    - "What classes does T001 have on Monday?"
    - "Show Monday schedule"
    """
    try:
        # Query timetable (deterministic)
        result = timetable_service.query_timetable(request.query, db)
        
        # Format as readable text
        formatted_text = timetable_service.format_timetable_text(result)
        
        return TimetableQueryResponse(
            **result,
            formatted_text=formatted_text
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timetable query failed: {str(e)}"
        )


@router.get("/teacher/{teacher_uid}", response_model=List[TimetableEntry])
async def get_teacher_timetable(
    teacher_uid: str,
    day: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get timetable for a specific teacher
    
    Args:
        teacher_uid: Teacher unique ID (e.g., T001)
        day: Optional day filter (e.g., Monday)
    """
    try:
        entries = timetable_service.get_timetable_by_teacher(
            teacher_uid=teacher_uid.upper(),
            day=day.capitalize() if day else None,
            db=db
        )
        
        return entries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timetable: {str(e)}"
        )


@router.get("/day/{day}", response_model=List[TimetableEntry])
async def get_day_timetable(
    day: str,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all timetable entries for a specific day
    
    Args:
        day: Day of week (e.g., Monday)
        department: Optional department filter
    """
    try:
        entries = timetable_service.get_timetable_by_day(
            day=day.capitalize(),
            department=department,
            db=db
        )
        
        return entries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timetable: {str(e)}"
        )


@router.get("/today", response_model=List[TimetableEntry])
async def get_today_schedule(
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get today's timetable schedule
    
    Automatically detects current day and returns all classes scheduled for today
    
    Query Parameters:
    - department: Optional department filter
    
    Returns all timetable entries for today
    """
    from datetime import datetime
    
    # Get current day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = days[datetime.now().weekday()]
    
    try:
        entries = timetable_service.get_timetable_by_day(
            day=today,
            department=department,
            db=db
        )
        
        return entries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve today's schedule: {str(e)}"
        )


@router.post("/test")
async def test_timetable(db: Session = Depends(get_db)):
    """
    Test endpoint to validate timetable functionality
    Creates sample data and tests queries
    """
    from app.models.timetable import Timetable
    from datetime import time
    
    try:
        # Clear existing test data
        db.query(Timetable).filter(Timetable.teacher_uid.like("TEST%")).delete()
        db.commit()
        
        # Create sample timetable entries
        sample_entries = [
            Timetable(
                teacher_uid="TEST001",
                teacher_name="Dr. John Smith",
                subject="Database Systems",
                day="Monday",
                start_time=time(9, 0),
                end_time=time(10, 30),
                classroom="Room 101",
                department="Computer Science"
            ),
            Timetable(
                teacher_uid="TEST001",
                teacher_name="Dr. John Smith",
                subject="Web Development",
                day="Monday",
                start_time=time(11, 0),
                end_time=time(12, 30),
                classroom="Room 102",
                department="Computer Science"
            ),
            Timetable(
                teacher_uid="TEST001",
                teacher_name="Dr. John Smith",
                subject="Database Systems",
                day="Wednesday",
                start_time=time(14, 0),
                end_time=time(15, 30),
                classroom="Room 101",
                department="Computer Science"
            ),
            Timetable(
                teacher_uid="TEST002",
                teacher_name="Prof. Jane Doe",
                subject="Machine Learning",
                day="Monday",
                start_time=time(9, 0),
                end_time=time(10, 30),
                classroom="Room 201",
                department="Computer Science"
            ),
        ]
        
        for entry in sample_entries:
            db.add(entry)
        db.commit()
        
        # Test queries
        test_queries = [
            "Show me timetable for TEST001",
            "What classes does TEST001 have on Monday?",
            "Show Monday schedule",
            "TEST002 Wednesday"
        ]
        
        results = []
        for query in test_queries:
            result = timetable_service.query_timetable(query, db)
            formatted = timetable_service.format_timetable_text(result)
            results.append({
                "query": query,
                "result": result,
                "formatted_text": formatted
            })
        
        return {
            "message": "Timetable test completed successfully",
            "sample_data_created": len(sample_entries),
            "test_results": results
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
