"""
Evaluation endpoints
Research and evaluation tools for RAG system
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.utils.evaluation import evaluation_logger
from app.services.rag_service import RAGService
from app.config import settings

router = APIRouter()


class EvaluationQueryRequest(BaseModel):
    """Evaluation query request"""
    query: str
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    top_k: Optional[int] = 3


class PrecisionAtKRequest(BaseModel):
    """Precision@K calculation request"""
    query: str
    relevant_doc_ids: List[str]
    k: int = 3


@router.post("/query")
async def evaluate_query(request: EvaluationQueryRequest):
    """
    Run a query with specific model configuration for evaluation
    
    Allows swapping embedding and LLM models to compare performance.
    All metrics are automatically logged.
    
    **Model Options:**
    - Embedding: `BAAI/bge-base-en-v1.5` (default), `sentence-transformers/all-MiniLM-L6-v2`
    - LLM: `phi3` (default), `llama2`, or any Ollama model
    """
    try:
        # Create RAG service with specified models
        rag = RAGService(
            embedding_model_name=request.embedding_model,
            llm_model_name=request.llm_model
        )
        
        # Run query (automatically logs metrics)
        result = rag.query(request.query, request.top_k)
        
        return {
            "message": "Query evaluated and logged",
            **result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/precision-at-k")
async def calculate_precision_at_k(request: PrecisionAtKRequest):
    """
    Calculate Precision@K for a query with known relevant documents
    
    Used for evaluation when you have ground truth relevance labels.
    
    Args:
        query: Search query
        relevant_doc_ids: List of document IDs that are relevant
        k: Number of top documents to consider
    """
    try:
        # Create RAG service
        rag = RAGService()
        rag.initialize()
        
        # Retrieve documents
        retrieval_result = rag.retrieve_context(request.query, top_k=request.k)
        retrieved_docs = retrieval_result["documents"]
        
        # Calculate Precision@K
        precision = evaluation_logger.calculate_precision_at_k(
            retrieved_docs=retrieved_docs,
            relevant_doc_ids=request.relevant_doc_ids,
            k=request.k
        )
        
        # Calculate Recall@K
        recall = evaluation_logger.calculate_recall_at_k(
            retrieved_docs=retrieved_docs,
            relevant_doc_ids=request.relevant_doc_ids,
            k=request.k
        )
        
        # Calculate MRR
        mrr = evaluation_logger.calculate_mrr(
            retrieved_docs=retrieved_docs,
            relevant_doc_ids=request.relevant_doc_ids
        )
        
        return {
            "query": request.query,
            "k": request.k,
            "metrics": {
                "precision_at_k": round(precision, 3),
                "recall_at_k": round(recall, 3),
                "mrr": round(mrr, 3)
            },
            "retrieved_docs": [
                {
                    "id": doc["id"],
                    "similarity_score": doc["similarity_score"],
                    "is_relevant": doc["id"] in request.relevant_doc_ids
                }
                for doc in retrieved_docs
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Precision@K calculation failed: {str(e)}"
        )


@router.get("/stats")
async def get_evaluation_stats(date: Optional[str] = Query(None, description="Date in YYYYMMDD format")):
    """
    Get evaluation statistics for a specific date
    
    Returns aggregated metrics including latency, similarity scores, and confidence distribution.
    
    Args:
        date: Date in YYYYMMDD format (defaults to today)
    """
    try:
        stats = evaluation_logger.get_summary_stats(date)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """
    Get available models for evaluation
    
    Returns lists of embedding and LLM models that can be used for comparison.
    """
    return {
        "embedding_models": {
            "default": settings.EMBEDDING_MODEL,
            "alternative": settings.EMBEDDING_MODEL_ALT,
            "description": "Sentence transformer models for text embedding"
        },
        "llm_models": {
            "default": settings.OLLAMA_MODEL,
            "alternative": settings.OLLAMA_MODEL_ALT,
            "description": "Ollama models for text generation",
            "note": "Any Ollama model can be used if installed locally"
        },
        "usage": {
            "example": {
                "query": "What is Python?",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "llm_model": "llama2"
            }
        }
    }


@router.post("/compare-models")
async def compare_models(query: str, top_k: int = 3):
    """
    Compare performance across different model configurations
    
    Runs the same query with different embedding and LLM models to compare:
    - Latency
    - Similarity scores
    - Answer quality (subjective)
    
    Args:
        query: Query to test
        top_k: Number of documents to retrieve
    """
    try:
        results = []
        
        # Configuration combinations to test
        configs = [
            {
                "name": "Default (BGE + Phi-3)",
                "embedding": settings.EMBEDDING_MODEL,
                "llm": settings.OLLAMA_MODEL
            },
            {
                "name": "MiniLM + Phi-3",
                "embedding": settings.EMBEDDING_MODEL_ALT,
                "llm": settings.OLLAMA_MODEL
            }
        ]
        
        for config in configs:
            try:
                rag = RAGService(
                    embedding_model_name=config["embedding"],
                    llm_model_name=config["llm"]
                )
                
                result = rag.query(query, top_k)
                
                results.append({
                    "configuration": config["name"],
                    "models": {
                        "embedding": config["embedding"],
                        "llm": config["llm"]
                    },
                    "latency": result["latency"],
                    "confidence": result["confidence"],
                    "max_similarity": result["max_similarity"],
                    "avg_similarity": result["avg_similarity"],
                    "answer_preview": result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"]
                })
                
            except Exception as e:
                results.append({
                    "configuration": config["name"],
                    "error": str(e)
                })
        
        return {
            "query": query,
            "top_k": top_k,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model comparison failed: {str(e)}"
        )
