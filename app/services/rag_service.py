"""
RAG (Retrieval-Augmented Generation) service
Implements document embedding, retrieval, and generation using:
- BAAI/bge-base-en-v1.5 for embeddings
- ChromaDB for vector storage
- Phi-3 Mini via Ollama for generation
"""

import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from groq import Groq
from app.config import settings
from app.utils.evaluation import evaluation_logger

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RAGService:
    """
    RAG service for document retrieval and AI-powered question answering
    with intelligent model fallback
    """
    
    # Ordered list of models to try (most stable first)
    # These are carefully selected for long-term availability
    AVAILABLE_MODELS = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "llama-2-70b-4096",
    ]
    
    def __init__(self, embedding_model_name: Optional[str] = None, llm_model_name: Optional[str] = None):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
        self._groq_client = None
        self._working_model = None

        self.embedding_model_name = embedding_model_name or settings.EMBEDDING_MODEL
        # Set primary model, but will try fallbacks if it fails
        self.primary_model = llm_model_name or getattr(settings, 'GROQ_MODEL', 'llama-3.1-70b-versatile')
        self.llm_model_name = self.primary_model
    
    def initialize(self):
        """
        Lazy initialization of models and vector store
        Called once on first use
        """
        if self._initialized:
            return
        
        print("🔧 Initializing RAG Service...")
        
        # Load embedding model
        print(f"   Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        print("   ✅ Embedding model loaded")
        
        # Initialize ChromaDB client
        print(f"   Initializing ChromaDB at: {settings.VECTOR_STORE_PATH}")
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=settings.VECTOR_STORE_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "EduVerse educational documents"}
        )
        print(f"   ✅ ChromaDB collection ready: {settings.CHROMA_COLLECTION_NAME}")
        
        self._initialized = True
        print("✅ RAG Service initialized successfully!")
    
    def add_documents(self, documents: List[Dict[str, str]]) -> bool:
        """
        Add documents to the vector store with embeddings
        
        Args:
            documents: List of dicts with 'id', 'text', and optional metadata
            
        Returns:
            True if successful
        """
        if not self._initialized:
            self.initialize()
        
        if not documents:
            return False
        
        # Extract texts and metadata
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        # Generate embeddings
        print(f"   Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        embeddings_list = embeddings.tolist()
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"   ✅ Added {len(documents)} documents to vector store")
        return True
    
    def retrieve_context(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query with similarity filtering
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve (default from config)
            similarity_threshold: Minimum similarity score (default from config)
            
        Returns:
            Dict with retrieved documents, scores, and confidence metrics
        """
        if not self._initialized:
            self.initialize()
        
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        if similarity_threshold is None:
            similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Format results and convert distance to similarity
        retrieved_docs = []
        all_scores = []
        
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert L2 distance to similarity score (0-1 range)
                # Lower distance = higher similarity
                similarity = 1.0 / (1.0 + distance)
                all_scores.append(similarity)
                
                doc = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": distance,
                    "similarity_score": similarity
                }
                
                # Filter by similarity threshold
                if similarity >= similarity_threshold:
                    retrieved_docs.append(doc)
        
        # Calculate confidence metrics
        max_score = max(all_scores) if all_scores else 0.0
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        # Log retrieval scores
        logger.info(f"Query: {query[:50]}...")
        logger.info(f"Retrieved: {len(results['documents'][0]) if results['documents'] else 0} docs")
        logger.info(f"After threshold filter: {len(retrieved_docs)} docs")
        logger.info(f"Max similarity: {max_score:.3f}, Avg similarity: {avg_score:.3f}")
        logger.info(f"Threshold: {similarity_threshold}")
        
        for i, doc in enumerate(retrieved_docs):
            logger.info(f"  Doc {i+1}: similarity={doc['similarity_score']:.3f}")
        
        return {
            "documents": retrieved_docs,
            "max_similarity": max_score,
            "avg_similarity": avg_score,
            "threshold_used": similarity_threshold,
            "total_retrieved": len(all_scores),
            "after_filtering": len(retrieved_docs)
        }
    
    def generate_with_groq(self, prompt: str) -> str:
        """
        Generate a response using the Groq API with intelligent fallback.
        Tries multiple models to ensure availability.
        """
        if self._groq_client is None:
            api_key = getattr(settings, 'GROQ_API_KEY', None)
            if not api_key:
                logger.error("GROQ_API_KEY is not set")
                return "⚠️ Groq API key not configured. Please set GROQ_API_KEY in .env file."
            self._groq_client = Groq(api_key=api_key)

        # If we have a working model, use it
        if self._working_model:
            try:
                return self._generate_with_model(prompt, self._working_model)
            except Exception as e:
                logger.warning(f"Previously working model {self._working_model} failed, trying fallbacks")
                self._working_model = None
        
        # Try each model in order
        models_to_try = [self.primary_model] + [m for m in self.AVAILABLE_MODELS if m != self.primary_model]
        last_error = None
        
        for model in models_to_try:
            logger.info(f"   Attempting with model: {model}")
            try:
                result = self._generate_with_model(prompt, model)
                # Check if result is an error message
                if result.startswith("⚠️"):
                    last_error = result
                    logger.warning(f"   Model {model} returned error: {result}")
                    continue
                # Success!
                self._working_model = model
                logger.info(f"   ✅ Successfully using model: {model}")
                return result
            except Exception as e:
                last_error = str(e)
                logger.warning(f"   Model {model} failed: {str(e)[:100]}")
                continue
        
        # All models failed - return last error or generic message
        logger.error(f"All Groq models failed. Last error: {last_error}")
        return "⚠️ AI service temporarily unavailable. Please try again or contact your instructor."
    
    def _generate_with_model(self, prompt: str, model: str) -> str:
        """
        Attempt to generate response with a specific model.
        Returns error message (starting with ⚠️) if model is unavailable.
        Raises exception for other errors.
        """
        try:
            chat_completion = self._groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational AI assistant. Answer questions strictly based on the provided context documents. If the context does not contain the answer, say so directly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=model,
                temperature=0.3,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e).lower()
            # Check if model is decommissioned/unavailable
            if any(keyword in error_str for keyword in ["decommissioned", "deprecated", "not supported", "does not exist", "invalid"]):
                logger.error(f"Model {model} unavailable: {str(e)[:100]}")
                return f"⚠️ Model {model} is no longer available"
            # For other errors, raise so we can try next model
            raise
    
    def build_rag_prompt(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Build a strict hallucination-controlled prompt with enhanced grounding
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            
        Returns:
            Formatted prompt string
        """
        # Build context section with relevance scores
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            score = doc.get('similarity_score', 0.0)
            context_parts.append(
                f"[Document {i}] (Relevance: {score:.2f})\n{doc['text']}"
            )
        
        context_text = "\n\n".join(context_parts)
        
        # Truncate if too long
        if len(context_text) > settings.RAG_MAX_CONTEXT_LENGTH:
            context_text = context_text[:settings.RAG_MAX_CONTEXT_LENGTH] + "..."
        
        # Build enhanced strict prompt
        prompt = f"""You are an educational AI assistant for EduVerse. Your role is to provide accurate, grounded answers based STRICTLY on the provided context.

**CRITICAL RULES - FOLLOW WITHOUT EXCEPTION:**

1. **ONLY use information explicitly stated in the context documents below**
2. **If the context does not contain the answer, you MUST respond with:**
   "I don't have enough information in my knowledge base to answer this question accurately."
3. **DO NOT:**
   - Make assumptions or inferences beyond what's stated
   - Add information from your general knowledge
   - Speculate or guess
   - Provide partial answers if you're unsure
4. **DO:**
   - Quote or paraphrase directly from the context
   - Cite document numbers when relevant (e.g., "According to Document 1...")
   - Be concise and direct
   - Acknowledge if information is incomplete

**CONTEXT DOCUMENTS:**
{context_text}

**USER QUESTION:** {query}

**YOUR ANSWER (based ONLY on the context above):**"""
        
        return prompt
    
    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline with hallucination control and evaluation logging
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            
        Returns:
            Dict with answer, sources, confidence metrics, latency, and metadata
        """
        if not self._initialized:
            self.initialize()
        
        # Start total timer
        total_start = time.time()
        
        # Step 1: Retrieve relevant documents with similarity filtering
        logger.info(f"🔍 Retrieving context for query: {question[:50]}...")
        retrieval_start = time.time()
        retrieval_result = self.retrieve_context(question, top_k)
        retrieval_latency = time.time() - retrieval_start
        
        context_docs = retrieval_result["documents"]
        max_similarity = retrieval_result["max_similarity"]
        avg_similarity = retrieval_result["avg_similarity"]
        
        # Step 2: Check confidence threshold
        if not context_docs or max_similarity < settings.RAG_MIN_CONFIDENCE:
            fallback_msg = (
                "I don't have enough relevant information in my knowledge base to answer this question accurately. "
                "Please try rephrasing your question or contact an administrator for assistance."
            )
            logger.warning(f"Low confidence retrieval: max_similarity={max_similarity:.3f}")
            
            total_latency = time.time() - total_start
            
            response = {
                "answer": fallback_msg,
                "sources": [],
                "context_used": 0,
                "confidence": "low",
                "max_similarity": max_similarity,
                "avg_similarity": avg_similarity,
                "threshold_used": retrieval_result["threshold_used"],
                "retrieval_stats": retrieval_result,
                "latency": {
                    "retrieval_ms": round(retrieval_latency * 1000, 2),
                    "generation_ms": 0.0,
                    "total_ms": round(total_latency * 1000, 2)
                }
            }
            
            # Log evaluation
            evaluation_logger.log_query(
                query=question,
                retrieval_latency=retrieval_latency,
                generation_latency=0.0,
                total_latency=total_latency,
                embedding_model=self.embedding_model_name,
                llm_model=self.llm_model_name,
                top_k=top_k or settings.RAG_TOP_K,
                similarity_threshold=retrieval_result["threshold_used"],
                retrieval_results=retrieval_result,
                response=response
            )
            
            return response
        
        logger.info(f"   ✅ Retrieved {len(context_docs)} relevant documents")
        logger.info(f"   Confidence: max={max_similarity:.3f}, avg={avg_similarity:.3f}")
        
        # Step 3: Build prompt
        prompt = self.build_rag_prompt(question, context_docs)
        
        # Step 4: Generate answer with error handling
        logger.info("🤖 Generating answer with Groq...")
        generation_start = time.time()
        try:
            answer = self.generate_with_groq(prompt)
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            answer = "⚠️ Unable to generate answer. Please check your Groq API key and model configuration."
        generation_latency = time.time() - generation_start
        logger.info("   ✅ Answer generated")
        
        # Determine confidence level
        if max_similarity >= 0.7:
            confidence = "high"
        elif max_similarity >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        total_latency = time.time() - total_start
        
        # Step 5: Format response
        response = {
            "answer": answer,
            "sources": [
                {
                    "id": doc["id"],
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "metadata": doc["metadata"],
                    "similarity_score": doc["similarity_score"],
                    "distance": doc["distance"]
                }
                for doc in context_docs
            ],
            "context_used": len(context_docs),
            "confidence": confidence,
            "max_similarity": max_similarity,
            "avg_similarity": avg_similarity,
            "threshold_used": retrieval_result["threshold_used"],
            "retrieval_stats": retrieval_result,
            "latency": {
                "retrieval_ms": round(retrieval_latency * 1000, 2),
                "generation_ms": round(generation_latency * 1000, 2),
                "total_ms": round(total_latency * 1000, 2)
            },
            "models_used": {
                "embedding": self.embedding_model_name,
                "llm": self.llm_model_name
            }
        }
        
        # Log evaluation
        evaluation_logger.log_query(
            query=question,
            retrieval_latency=retrieval_latency,
            generation_latency=generation_latency,
            total_latency=total_latency,
            embedding_model=self.embedding_model_name,
            llm_model=self.llm_model_name,
            top_k=top_k or settings.RAG_TOP_K,
            similarity_threshold=retrieval_result["threshold_used"],
            retrieval_results=retrieval_result,
            response=response
        )
        
        return response
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        if not self._initialized:
            self.initialize()
        
        count = self.collection.count()
        return {
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "document_count": count,
            "embedding_model": settings.EMBEDDING_MODEL,
            "ollama_model": settings.OLLAMA_MODEL
        }


# Global service instance
rag_service = RAGService()


# Initialize with dummy documents for testing
def initialize_with_dummy_data():
    """Initialize RAG service with hardcoded dummy documents for testing"""
    
    dummy_documents = [
        {
            "id": "doc_001",
            "text": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "metadata": {"category": "Programming", "topic": "Python Basics"}
        },
        {
            "id": "doc_002",
            "text": "Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
            "metadata": {"category": "AI/ML", "topic": "Machine Learning Introduction"}
        },
        {
            "id": "doc_003",
            "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It is one of the fastest Python frameworks available and provides automatic interactive API documentation.",
            "metadata": {"category": "Web Development", "topic": "FastAPI"}
        },
        {
            "id": "doc_004",
            "text": "Database normalization is the process of organizing data in a database to reduce redundancy and improve data integrity. The most common normal forms are 1NF, 2NF, 3NF, and BCNF (Boyce-Codd Normal Form).",
            "metadata": {"category": "Database", "topic": "Normalization"}
        },
        {
            "id": "doc_005",
            "text": "REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs use HTTP requests to perform CRUD operations: Create (POST), Read (GET), Update (PUT/PATCH), and Delete (DELETE).",
            "metadata": {"category": "Web Development", "topic": "REST API"}
        },
        {
            "id": "doc_006",
            "text": "Vector databases store data as high-dimensional vectors, which are mathematical representations of features or attributes. They enable similarity search and are essential for applications like recommendation systems, semantic search, and RAG (Retrieval-Augmented Generation).",
            "metadata": {"category": "Database", "topic": "Vector Databases"}
        }
    ]
    
    print("\n📚 Initializing RAG service with dummy documents...")
    rag_service.initialize()
    rag_service.add_documents(dummy_documents)
    print(f"✅ RAG service ready with {len(dummy_documents)} dummy documents\n")
