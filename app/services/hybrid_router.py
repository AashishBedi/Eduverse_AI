"""
Hybrid query router for timetable queries
Routes between SQL (structured) and vector search (semantic)
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.utils.query_analyzer import analyze_query, QueryIntent
from app.services.timetable_service import timetable_service
from app.services.rag_service import rag_service


def route_timetable_query(
    query: str,
    db: Session,
    use_llm_formatting: bool = False
) -> Dict[str, Any]:
    """
    Route timetable query between SQL and vector search
    
    Routing logic:
    - Teacher ID detected → SQL direct lookup
    - Day detected (no teacher) → SQL day query
    - Semantic query → Vector search + LLM
    
    Args:
        query: User query
        db: Database session
        use_llm_formatting: Whether to use LLM for formatting SQL results
        
    Returns:
        Unified response with routing metadata
    """
    # Analyze query
    analysis = analyze_query(query)
    
    # Route based on intent
    if analysis.intent == QueryIntent.TEACHER_LOOKUP:
        return handle_teacher_lookup(query, analysis, db, use_llm_formatting)
    
    elif analysis.intent == QueryIntent.DAY_LOOKUP:
        return handle_day_lookup(query, analysis, db, use_llm_formatting)
    
    else:  # SEMANTIC
        return handle_semantic_query(query)


def handle_teacher_lookup(
    query: str,
    analysis,
    db: Session,
    use_llm_formatting: bool
) -> Dict[str, Any]:
    """
    Handle teacher-based lookup using SQL
    
    Args:
        query: Original query
        analysis: Query analysis result
        db: Database session
        use_llm_formatting: Use LLM for natural language formatting
        
    Returns:
        Structured response with SQL results
    """
    # Get timetable entries from SQL
    entries = timetable_service.get_timetable_by_teacher(
        teacher_uid=analysis.teacher_id,
        day=analysis.day,
        db=db
    )
    
    if not entries:
        # No results found
        if analysis.day:
            answer = f"No timetable entries found for teacher {analysis.teacher_id} on {analysis.day}."
        else:
            answer = f"No timetable entries found for teacher {analysis.teacher_id}."
        
        return {
            "routing_method": "sql",
            "query_type": "teacher_lookup",
            "answer": answer,
            "data": {
                "teacher_uid": analysis.teacher_id,
                "day": analysis.day,
                "entries": [],
                "count": 0
            },
            "sources": [],
            "metadata": {
                "deterministic": True,
                "llm_used": False
            }
        }
    
    # Format response
    if use_llm_formatting:
        # Use LLM to format SQL results naturally
        formatted_text = format_with_llm(entries, analysis)
    else:
        # Use structured formatting
        result_data = {
            "query_type": "teacher_lookup",
            "teacher_uid": analysis.teacher_id,
            "day": analysis.day,
            "entries": entries,
            "count": len(entries)
        }
        formatted_text = timetable_service.format_timetable_text(result_data)
    
    return {
        "routing_method": "sql",
        "query_type": "teacher_lookup",
        "answer": formatted_text,
        "data": {
            "teacher_uid": analysis.teacher_id,
            "day": analysis.day,
            "entries": entries,
            "count": len(entries)
        },
        "sources": [],
        "metadata": {
            "deterministic": True,
            "llm_used": use_llm_formatting
        }
    }


def handle_day_lookup(
    query: str,
    analysis,
    db: Session,
    use_llm_formatting: bool
) -> Dict[str, Any]:
    """
    Handle day-based lookup using SQL
    
    Args:
        query: Original query
        analysis: Query analysis result
        db: Database session
        use_llm_formatting: Use LLM for formatting
        
    Returns:
        Structured response with SQL results
    """
    # Get timetable entries for the day
    entries = timetable_service.get_timetable_by_day(
        day=analysis.day,
        db=db
    )
    
    if not entries:
        answer = f"No timetable entries found for {analysis.day}."
        return {
            "routing_method": "sql",
            "query_type": "day_lookup",
            "answer": answer,
            "data": {
                "day": analysis.day,
                "entries": [],
                "count": 0
            },
            "sources": [],
            "metadata": {
                "deterministic": True,
                "llm_used": False
            }
        }
    
    # Format response
    result_data = {
        "query_type": "day_only",
        "teacher_uid": None,
        "day": analysis.day,
        "entries": entries,
        "count": len(entries)
    }
    formatted_text = timetable_service.format_timetable_text(result_data)
    
    return {
        "routing_method": "sql",
        "query_type": "day_lookup",
        "answer": formatted_text,
        "data": {
            "day": analysis.day,
            "entries": entries,
            "count": len(entries)
        },
        "sources": [],
        "metadata": {
            "deterministic": True,
            "llm_used": False
        }
    }


def handle_semantic_query(query: str) -> Dict[str, Any]:
    """
    Handle semantic query using vector search + LLM
    
    Args:
        query: User query
        
    Returns:
        RAG response with sources
    """
    # Use RAG service for semantic search
    result = rag_service.query(query, top_k=3)
    
    return {
        "routing_method": "vector",
        "query_type": "semantic",
        "answer": result["answer"],
        "data": {},
        "sources": result["sources"],
        "metadata": {
            "deterministic": False,
            "llm_used": True,
            "context_used": result.get("context_used", False)
        }
    }


def format_with_llm(entries: list, analysis) -> str:
    """
    Format SQL results using LLM for natural language
    
    Args:
        entries: Timetable entries from SQL
        analysis: Query analysis
        
    Returns:
        Natural language formatted response
    """
    # Build structured context
    context = f"Teacher ID: {analysis.teacher_id}\n"
    if analysis.day:
        context += f"Day: {analysis.day}\n"
    
    context += "\nTimetable entries:\n"
    for entry in entries:
        context += (
            f"- {entry['day']}: {entry['start_time']} - {entry['end_time']}, "
            f"{entry['subject']} in {entry['classroom']}\n"
        )
    
    # Use LLM to format naturally
    prompt = f"Format this timetable information in a clear, natural way:\n\n{context}"
    
    # Call LLM (simplified - in production, use proper LLM service)
    # For now, return structured format
    result_data = {
        "query_type": "teacher_lookup",
        "teacher_uid": analysis.teacher_id,
        "day": analysis.day,
        "entries": entries,
        "count": len(entries)
    }
    return timetable_service.format_timetable_text(result_data)
