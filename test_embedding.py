from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

text = "What is the admission deadline?"
embedding = model.encode(text)

print("Embedding length:", len(embedding))
