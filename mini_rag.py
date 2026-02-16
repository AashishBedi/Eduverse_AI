import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json

# -----------------------------
# 1. Load Embedding Model
# -----------------------------
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# -----------------------------
# 2. Create Chroma Client
# -----------------------------
client = chromadb.Client()
collection = client.get_or_create_collection(name="eduverse_demo")

# -----------------------------
# 3. Hardcoded University Documents
# -----------------------------
documents = [
    "The admission deadline for 2026 is 30 June.",
    "Minimum attendance required is 75 percent to appear in exams.",
    "The examination form fee is 2000 INR for undergraduate students."
]

# -----------------------------
# 4. Embed and Store Documents
# -----------------------------
embeddings = model.encode(documents).tolist()

collection.add(
    documents=documents,
    embeddings=embeddings,
    ids=["doc1", "doc2", "doc3"]
)

print("Documents stored successfully.\n")

# -----------------------------
# 5. Take User Query
# -----------------------------
query = input("Ask your question: ")

query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

retrieved_docs = results["documents"][0]

print("\nRetrieved Context:")
for doc in retrieved_docs:
    print("-", doc)

# -----------------------------
# 6. Build Strict Prompt
# -----------------------------
context_text = "\n".join(retrieved_docs)

prompt = f"""
You are a university assistant.
Answer ONLY using the provided context.
If the answer is not found, say:
"The information is not available in the uploaded university data."

Context:
{context_text}

Question:
{query}
"""

# -----------------------------
# 7. Send to Ollama (TinyLlama)
# -----------------------------
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "phi3:mini",
        "prompt": prompt,
        "stream": False
    }
)

answer = response.json()["response"]

print("\nAI Response:\n")
print(answer)
