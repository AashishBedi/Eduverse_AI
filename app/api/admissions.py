"""
Admissions API endpoints
Handles structured admission data retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db
from app.models.admission import Admission

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_admissions(
    department: str = None,
    academic_year: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all admission programs
    
    Query Parameters:
    - department: Filter by department (optional)
    - academic_year: Filter by academic year (optional)
    
    Returns structured admission data from database
    """
    query = db.query(Admission)
    
    if department:
        query = query.filter(Admission.department == department)
    
    if academic_year:
        query = query.filter(Admission.academic_year == academic_year)
    
    admissions = query.all()
    
    if not admissions:
        return []
    
    # Convert to dict
    result = []
    for admission in admissions:
        result.append({
            "program_name": admission.program_name,
            "eligibility": admission.eligibility,
            "duration": admission.duration,
            "intake": admission.intake,
            "admission_process": admission.admission_process,
            "contact_email": admission.contact_email,
            "department": admission.department,
            "academic_year": admission.academic_year
        })
    
    return result


@router.get("/{program_name}", response_model=Dict[str, Any])
async def get_admission_by_program(
    program_name: str,
    db: Session = Depends(get_db)
):
    """
    Get admission details for a specific program
    
    Path Parameters:
    - program_name: Name of the program
    
    Returns detailed admission information
    """
    admission = db.query(Admission).filter(
        Admission.program_name.ilike(f"%{program_name}%")
    ).first()
    
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No admission information found for program: {program_name}"
        )
    
    return {
        "program_name": admission.program_name,
        "eligibility": admission.eligibility,
        "duration": admission.duration,
        "intake": admission.intake,
        "admission_process": admission.admission_process,
        "contact_email": admission.contact_email,
        "department": admission.department,
        "academic_year": admission.academic_year
    }
