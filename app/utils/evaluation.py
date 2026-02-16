"""
Evaluation logging module
Tracks performance metrics for RAG system evaluation
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config import settings


class EvaluationLogger:
    """
    Logs evaluation metrics for RAG system performance analysis
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize evaluation logger
        
        Args:
            log_dir: Directory for evaluation logs (default from config)
        """
        self.log_dir = log_dir or settings.EVALUATION_LOG_PATH
        self.enabled = settings.ENABLE_EVALUATION_LOGGING
        
        if self.enabled:
            os.makedirs(self.log_dir, exist_ok=True)
            self.log_file = os.path.join(
                self.log_dir,
                f"evaluation_{datetime.now().strftime('%Y%m%d')}.jsonl"
            )
    
    def log_query(
        self,
        query: str,
        retrieval_latency: float,
        generation_latency: float,
        total_latency: float,
        embedding_model: str,
        llm_model: str,
        top_k: int,
        similarity_threshold: float,
        retrieval_results: Dict[str, Any],
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a single query evaluation
        
        Args:
            query: User query
            retrieval_latency: Time for retrieval (seconds)
            generation_latency: Time for generation (seconds)
            total_latency: Total time (seconds)
            embedding_model: Embedding model used
            llm_model: LLM model used
            top_k: Number of documents retrieved
            similarity_threshold: Threshold used
            retrieval_results: Retrieval results dict
            response: Final response dict
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "latency": {
                "retrieval_ms": round(retrieval_latency * 1000, 2),
                "generation_ms": round(generation_latency * 1000, 2),
                "total_ms": round(total_latency * 1000, 2)
            },
            "models": {
                "embedding": embedding_model,
                "llm": llm_model
            },
            "parameters": {
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            },
            "retrieval": {
                "total_retrieved": retrieval_results.get("total_retrieved", 0),
                "after_filtering": retrieval_results.get("after_filtering", 0),
                "max_similarity": retrieval_results.get("max_similarity", 0.0),
                "avg_similarity": retrieval_results.get("avg_similarity", 0.0)
            },
            "response": {
                "confidence": response.get("confidence", "unknown"),
                "context_used": response.get("context_used", 0),
                "answer_length": len(response.get("answer", ""))
            },
            "metadata": metadata or {}
        }
        
        # Append to JSONL file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def calculate_precision_at_k(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: List[str],
        k: int
    ) -> float:
        """
        Calculate Precision@K metric
        
        Args:
            retrieved_docs: List of retrieved documents (ordered by relevance)
            relevant_doc_ids: List of known relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Precision@K score (0.0 to 1.0)
        """
        if not retrieved_docs or k <= 0:
            return 0.0
        
        # Get top K documents
        top_k_docs = retrieved_docs[:k]
        
        # Count how many are relevant
        relevant_count = sum(
            1 for doc in top_k_docs 
            if doc.get("id") in relevant_doc_ids
        )
        
        return relevant_count / k
    
    def calculate_recall_at_k(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: List[str],
        k: int
    ) -> float:
        """
        Calculate Recall@K metric
        
        Args:
            retrieved_docs: List of retrieved documents
            relevant_doc_ids: List of known relevant document IDs
            k: Number of top documents to consider
            
        Returns:
            Recall@K score (0.0 to 1.0)
        """
        if not relevant_doc_ids or k <= 0:
            return 0.0
        
        # Get top K documents
        top_k_docs = retrieved_docs[:k]
        
        # Count how many relevant docs were retrieved
        relevant_count = sum(
            1 for doc in top_k_docs 
            if doc.get("id") in relevant_doc_ids
        )
        
        return relevant_count / len(relevant_doc_ids)
    
    def calculate_mrr(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: List[str]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR)
        
        Args:
            retrieved_docs: List of retrieved documents
            relevant_doc_ids: List of known relevant document IDs
            
        Returns:
            MRR score
        """
        for i, doc in enumerate(retrieved_docs, 1):
            if doc.get("id") in relevant_doc_ids:
                return 1.0 / i
        
        return 0.0
    
    def get_summary_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics from evaluation logs
        
        Args:
            date: Date string (YYYYMMDD), defaults to today
            
        Returns:
            Summary statistics dict
        """
        if not self.enabled:
            return {"error": "Evaluation logging is disabled"}
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        log_file = os.path.join(self.log_dir, f"evaluation_{date}.jsonl")
        
        if not os.path.exists(log_file):
            return {"error": f"No evaluation log found for date {date}"}
        
        # Read all entries
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                entries.append(json.loads(line))
        
        if not entries:
            return {"total_queries": 0}
        
        # Calculate statistics
        total_queries = len(entries)
        
        retrieval_latencies = [e["latency"]["retrieval_ms"] for e in entries]
        generation_latencies = [e["latency"]["generation_ms"] for e in entries]
        total_latencies = [e["latency"]["total_ms"] for e in entries]
        
        max_similarities = [e["retrieval"]["max_similarity"] for e in entries]
        avg_similarities = [e["retrieval"]["avg_similarity"] for e in entries]
        
        confidence_counts = {}
        for e in entries:
            conf = e["response"]["confidence"]
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        return {
            "total_queries": total_queries,
            "date": date,
            "latency": {
                "retrieval": {
                    "min_ms": min(retrieval_latencies),
                    "max_ms": max(retrieval_latencies),
                    "avg_ms": sum(retrieval_latencies) / len(retrieval_latencies),
                    "median_ms": sorted(retrieval_latencies)[len(retrieval_latencies) // 2]
                },
                "generation": {
                    "min_ms": min(generation_latencies),
                    "max_ms": max(generation_latencies),
                    "avg_ms": sum(generation_latencies) / len(generation_latencies),
                    "median_ms": sorted(generation_latencies)[len(generation_latencies) // 2]
                },
                "total": {
                    "min_ms": min(total_latencies),
                    "max_ms": max(total_latencies),
                    "avg_ms": sum(total_latencies) / len(total_latencies),
                    "median_ms": sorted(total_latencies)[len(total_latencies) // 2]
                }
            },
            "similarity": {
                "max": {
                    "min": min(max_similarities),
                    "max": max(max_similarities),
                    "avg": sum(max_similarities) / len(max_similarities)
                },
                "avg": {
                    "min": min(avg_similarities),
                    "max": max(avg_similarities),
                    "avg": sum(avg_similarities) / len(avg_similarities)
                }
            },
            "confidence_distribution": confidence_counts,
            "models_used": {
                "embedding": list(set(e["models"]["embedding"] for e in entries)),
                "llm": list(set(e["models"]["llm"] for e in entries))
            }
        }


# Global logger instance
evaluation_logger = EvaluationLogger()
