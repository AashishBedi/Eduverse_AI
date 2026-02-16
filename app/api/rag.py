"""
RAG test endpoints
Test endpoint to verify RAG pipeline functionality
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.rag_service import rag_service, initialize_with_dummy_data

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """RAG query request schema"""
    question: str
    top_k: Optional[int] = None


class RAGQueryResponse(BaseModel):
    """RAG query response schema"""
    answer: str
    sources: List[Dict[str, Any]]
    context_used: int


class RAGStatsResponse(BaseModel):
    """RAG statistics response schema"""
    collection_name: str
    document_count: int
    embedding_model: str
    ollama_model: str


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """
    Test RAG pipeline with a question
    
    This endpoint demonstrates the complete RAG workflow:
    1. Retrieves relevant documents from vector store
    2. Builds context-aware prompt
    3. Generates answer using Ollama
    4. Returns answer with sources
    """
    try:
        result = rag_service.query(
            question=request.question,
            top_k=request.top_k
        )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats():
    """
    Get RAG service statistics
    
    Returns information about the vector store and models
    """
    try:
        stats = rag_service.get_collection_stats()
        return RAGStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RAG stats: {str(e)}"
        )


@router.post("/initialize-dummy")
async def initialize_dummy():
    """
    Initialize RAG service with dummy documents for testing
    
    This endpoint loads hardcoded educational documents into the vector store
    """
    try:
        initialize_with_dummy_data()
        stats = rag_service.get_collection_stats()
        
        return {
            "message": "RAG service initialized with dummy documents",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize dummy data: {str(e)}"
        )
