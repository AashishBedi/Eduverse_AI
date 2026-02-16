"""
Chat orchestration service
Mode-aware routing to prevent cross-domain contamination
"""

from typing import Dict, Any, Optional, Literal
from enum import Enum
from sqlalchemy.orm import Session
from app.services.rag_service import rag_service
from app.services.timetable_service import timetable_service


class ChatMode(str, Enum):
    """Supported chat modes"""
    ADMISSIONS = "admissions"
    TIMETABLE = "timetable"
    FEES = "fees"
    REGULATIONS = "regulations"
    GENERAL = "general"


class ChatOrchestrator:
    """
    Orchestrates chat requests across different services
    Ensures strict separation to prevent cross-domain contamination
    """
    
    def __init__(self):
        # Mode-specific configurations
        self.structured_modes = {ChatMode.ADMISSIONS, ChatMode.TIMETABLE, ChatMode.FEES}
        self.rag_modes = {ChatMode.REGULATIONS, ChatMode.GENERAL}
    
    def handle_admissions_mode(
        self, 
        query: str, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Handle admissions queries using structured database retrieval
        NO RAG, NO debug information, clean formatted responses
        
        Args:
            query: User query
            db: Database session
            
        Returns:
            Clean structured response
        """
        from app.services.admissions_service import admissions_service
        
        # Use structured admissions service
        result = admissions_service.query_admissions(query, db)
        
        return {
            "mode": ChatMode.ADMISSIONS,
            "response_type": "structured",
            "answer": result["answer"],
            "data": {
                "query_type": result["query_type"],
                "program_name": result.get("program_name")
            },
            "sources": [],
            "metadata": {
                "deterministic": result["deterministic"],
                "llm_used": False,
                "service": "admissions_service",
                "routing_method": "structured_db_query"
            }
        }
    
    def handle_fees_mode(
        self, 
        query: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Handle fees queries using structured database retrieval
        NO RAG, clean formatted responses
        
        Args:
            query: User query
            db: Database session
            
        Returns:
            Clean structured response
        """
        from app.services.fees_service import fees_service
        
        # Use structured fees service
        result = fees_service.query_fees(query, db)
        
        return {
            "mode": ChatMode.FEES,
            "response_type": "structured",
            "answer": result["answer"],
            "data": {
                "query_type": result["query_type"],
                "program_name": result.get("program_name")
            },
            "sources": [],
            "metadata": {
                "deterministic": result["deterministic"],
                "llm_used": False,
                "service": "fees_service",
                "routing_method": "structured_db_query"
            }
        }
    
    def handle_timetable_mode(
        self, 
        query: str, 
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Handle timetable queries using hybrid routing
        
        Routes between:
        - SQL for structured queries (teacher ID, day)
        - Vector search for semantic queries
        
        Args:
            query: User query
            db: Database session
            
        Returns:
            Unified response with routing metadata
        """
        from app.services.hybrid_router import route_timetable_query
        
        # Use hybrid router
        result = route_timetable_query(query, db)
        
        return {
            "mode": ChatMode.TIMETABLE,
            "response_type": result["routing_method"],
            "answer": result["answer"],
            "data": result.get("data", {}),
            "sources": result.get("sources", []),
            "metadata": {
                "routing_method": result["routing_method"],
                "query_type": result.get("query_type"),
                "deterministic": result["metadata"]["deterministic"],
                "llm_used": result["metadata"]["llm_used"],
                "service": "hybrid_router"
            }
        }
    
    def handle_rag_mode(
        self, 
        query: str, 
        mode: ChatMode,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Handle RAG-based queries (regulations, general)
        Uses LLM with retrieved context
        
        Args:
            query: User query
            mode: Chat mode
            top_k: Number of documents to retrieve
            
        Returns:
            RAG response with sources
        """
        # Use RAG service with mode-specific context filtering
        result = rag_service.query(query, top_k)
        
        return {
            "mode": mode,
            "response_type": "rag",
            "answer": result["answer"],
            "data": {},
            "sources": result["sources"],
            "metadata": {
                "deterministic": False,
                "llm_used": True,
                "service": "rag_service",
                "context_used": result["context_used"]
            }
        }
    
    def chat(
        self, 
        mode: ChatMode, 
        query: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Unified chat interface with mode-aware routing
        Ensures strict separation between different query types
        
        Args:
            mode: Chat mode (admissions, timetable, fees, regulations, general)
            query: User query
            db: Database session (for structured queries)
            
        Returns:
            Unified response format
        """
        # Route based on mode
        if mode == ChatMode.ADMISSIONS:
            return self.handle_admissions_mode(query, db)
        
        elif mode == ChatMode.FEES:
            return self.handle_fees_mode(query, db)
        
        elif mode == ChatMode.TIMETABLE:
            return self.handle_timetable_mode(query, db)
        
        elif mode in self.rag_modes:
            return self.handle_rag_mode(query, mode)
        
        else:
            # Fallback to general RAG
            return self.handle_rag_mode(query, ChatMode.GENERAL)
    
    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about available modes"""
        return {
            "modes": [mode.value for mode in ChatMode],
            "structured_modes": [mode.value for mode in self.structured_modes],
            "rag_modes": [mode.value for mode in self.rag_modes],
            "descriptions": {
                "admissions": "Admission-related queries (structured database retrieval)",
                "timetable": "Teacher schedule queries (hybrid: SQL + RAG)",
                "fees": "Fee-related queries (structured database retrieval)",
                "regulations": "Academic regulations queries (uses RAG)",
                "general": "General educational queries (uses RAG)"
            }
        }


# Global orchestrator instance
chat_orchestrator = ChatOrchestrator()
