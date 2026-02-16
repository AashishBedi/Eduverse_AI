"""
Fees API endpoints
Handles structured fee data retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db
from app.models.fee import Fee

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_fees(
    department: str = None,
    academic_year: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all fee structures
    
    Query Parameters:
    - department: Filter by department (optional)
    - academic_year: Filter by academic year (optional)
    
    Returns structured fee data from database
    """
    query = db.query(Fee)
    
    if department:
        query = query.filter(Fee.department == department)
    
    if academic_year:
        query = query.filter(Fee.academic_year == academic_year)
    
    fees = query.all()
    
    if not fees:
        return []
    
    # Convert to dict
    result = []
    for fee in fees:
        result.append({
            "program_name": fee.program_name,
            "tuition_fee": fee.tuition_fee,
            "hostel_fee": fee.hostel_fee,
            "exam_fee": fee.exam_fee,
            "other_fee": fee.other_fee,
            "total_fee": fee.total_fee,
            "academic_year": fee.academic_year,
            "department": fee.department
        })
    
    return result


@router.get("/{program_name}", response_model=Dict[str, Any])
async def get_fee_by_program(
    program_name: str,
    db: Session = Depends(get_db)
):
    """
    Get fee structure for a specific program
    
    Path Parameters:
    - program_name: Name of the program
    
    Returns detailed fee breakdown
    """
    fee = db.query(Fee).filter(
        Fee.program_name.ilike(f"%{program_name}%")
    ).first()
    
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No fee information found for program: {program_name}"
        )
    
    return {
        "program_name": fee.program_name,
        "tuition_fee": fee.tuition_fee,
        "hostel_fee": fee.hostel_fee,
        "exam_fee": fee.exam_fee,
        "other_fee": fee.other_fee,
        "total_fee": fee.total_fee,
        "academic_year": fee.academic_year,
        "department": fee.department
    }
