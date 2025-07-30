import os
import sys
import json
import pickle

# Aggiunge il path dei pacchetti user (Linux/macOS)
user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

# === Dipendenze ===
try:
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.chains import RetrievalQA
    from langchain_community.llms import Ollama
except ImportError as e:
    print(f"Dipendenza mancante: {e}")
    print("Installa con:\n pip install langchain faiss-cpu sentence-transformers openai")
    sys.exit(1)

# === Config ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "blender_chunks.json")
INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")
EMBEDDING_MODEL = "intfloat/e5-large-v2"
QUERY = "How do I apply a bump map in Blender?"

# === 1. Caricamento JSON ===
print("[INFO] Caricamento chunk da JSON...")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    raw_chunks = json.load(f)

# === 2. Conversione in Document() ===
print("[INFO] Creazione Document objects...")
docs = []
for entry in raw_chunks:
    metadata = {k: v for k, v in entry.items() if k != "content"}
    docs.append(Document(page_content=entry["content"], metadata=metadata))

# === 3. Embedding ===
print(f"[INFO] Calcolo embeddings con: {EMBEDDING_MODEL}")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# === 4. FAISS ===
print("[INFO] Indicizzazione FAISS...")
db = FAISS.from_documents(docs, embeddings)
retriever = db.as_retriever(search_kwargs={"k": 6})

# === 5. Salvataggio su disco ===
print(f"[INFO] Salvataggio indice FAISS in: {INDEX_PATH}")
with open(INDEX_PATH, "wb") as f:
    pickle.dump({
        "index": db.index,
        "texts": [doc.page_content for doc in docs],
        "metadatas": [doc.metadata for doc in docs]
    }, f)
print("Indice salvato correttamente.")

# === 6. LLM ===
print("[INFO] Avvio LLM...")
llm = Ollama(model="llama3:instruct", temperature=0)

# === 7. RetrievalQA ===
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

# === 8. Esecuzione ===
print(f"\nDomanda: {QUERY}\n")
res = qa_chain.invoke(QUERY)

print(f"\nRisposta:\n{res['result']}\n")
print("Fonti:")
for doc in res['source_documents']:
    print(f"→ {doc.metadata.get('chapter', '')} - {doc.metadata.get('topic', '')}")
