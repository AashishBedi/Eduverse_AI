"""
Unified chat endpoint
Mode-aware routing with strict separation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from sqlalchemy.orm import Session
from app.services.chat_orchestrator import chat_orchestrator, ChatMode
from app.db.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    """Unified chat request schema"""
    mode: Literal["admissions", "timetable", "fees", "regulations", "general"]
    query: str


class ChatResponse(BaseModel):
    """Unified chat response schema"""
    mode: str
    response_type: str  # "structured" or "rag"
    answer: str
    data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/", response_model=ChatResponse)
async def unified_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Unified chat endpoint with mode-aware routing
    
    Modes:
    - **admissions**: Admission-related queries (uses RAG)
    - **timetable**: Teacher schedule queries (deterministic, no LLM)
    - **fees**: Fee-related queries (hybrid: structured + RAG)
    - **regulations**: Academic regulations queries (uses RAG)
    - **general**: General educational queries (uses RAG)
    
    The routing ensures strict separation to prevent cross-domain contamination.
    
    Examples:
    ```json
    {
      "mode": "timetable",
      "query": "Show me timetable for T001 on Monday"
    }
    ```
    
    ```json
    {
      "mode": "admissions",
      "query": "What are the admission requirements?"
    }
    ```
    """
    try:
        # Convert mode string to enum
        mode_enum = ChatMode(request.mode)
        
        # Route to appropriate handler
        result = chat_orchestrator.chat(
            mode=mode_enum,
            query=request.query,
            db=db
        )
        
        return ChatResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {request.mode}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )


@router.get("/modes")
async def get_available_modes():
    """
    Get information about available chat modes
    
    Returns descriptions and categorization of all supported modes
    """
    return chat_orchestrator.get_mode_info()


@router.post("/test")
async def test_unified_chat(db: Session = Depends(get_db)):
    """
    Test endpoint to validate unified chat functionality
    Tests all modes with sample queries
    """
    from app.services.rag_service import initialize_with_dummy_data
    from app.models.timetable import Timetable
    from datetime import time
    
    try:
        # Initialize RAG with dummy data
        print("Initializing RAG service...")
        initialize_with_dummy_data()
        
        # Create sample timetable data
        print("Creating sample timetable data...")
        db.query(Timetable).filter(Timetable.teacher_uid.like("TEST%")).delete()
        db.commit()
        
        sample_timetable = Timetable(
            teacher_uid="TEST001",
            teacher_name="Dr. Test Teacher",
            subject="Test Subject",
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            classroom="Room 101",
            department="Computer Science"
        )
        db.add(sample_timetable)
        db.commit()
        
        # Test queries for each mode
        test_cases = [
            {
                "mode": ChatMode.TIMETABLE,
                "query": "Show me timetable for TEST001 on Monday"
            },
            {
                "mode": ChatMode.ADMISSIONS,
                "query": "What is Python?"
            },
            {
                "mode": ChatMode.GENERAL,
                "query": "Explain FastAPI"
            },
            {
                "mode": ChatMode.FEES,
                "query": "What is the tuition fee?"
            },
            {
                "mode": ChatMode.REGULATIONS,
                "query": "Tell me about REST APIs"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                result = chat_orchestrator.chat(
                    mode=test_case["mode"],
                    query=test_case["query"],
                    db=db
                )
                results.append({
                    "mode": test_case["mode"].value,
                    "query": test_case["query"],
                    "success": True,
                    "response_type": result["response_type"],
                    "answer_preview": result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"],
                    "metadata": result["metadata"]
                })
            except Exception as e:
                results.append({
                    "mode": test_case["mode"].value,
                    "query": test_case["query"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "message": "Unified chat test completed",
            "modes_tested": len(test_cases),
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
