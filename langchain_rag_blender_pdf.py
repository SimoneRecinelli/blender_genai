import os
import sys
import pickle

# Aggiunge i pacchetti user al path di Blender
user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

# === Dipendenze ===
try:
    from langchain_community.document_loaders import PyMuPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.chains import RetrievalQA
    from langchain_community.llms import Ollama
except ImportError as e:
    print(f"Dipendenza mancante: {e}")
    print("Installa con:\n pip install langchain faiss-cpu sentence-transformers PyMuPDF openai")
    sys.exit(1)

# === Config ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "book_sliced.pdf")
INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")
EMBEDDING_MODEL = "intfloat/e5-large-v2"
QUERY = "How can you use the geometry proximity node in Blender?"

# === 1. Caricamento PDF ===
# print("[INFO] Caricamento PDF...")
loader = PyMuPDFLoader(PDF_PATH)
docs = loader.load()

# === 2. Suddivisione in chunk ===
# print("[INFO] Suddivisione in chunk...")
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# === 3. Embedding model ===
# print(f"[INFO] Calcolo embeddings con: {EMBEDDING_MODEL}")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# === 4. Costruzione FAISS retriever ===
# print("[INFO] Indicizzazione FAISS...")
db = FAISS.from_documents(chunks, embeddings)
retriever = db.as_retriever(search_kwargs={"k": 6})

# === 💾 5. Salvataggio su disco ===
# print(f"[INFO] Salvataggio indice in: {INDEX_PATH}")
try:
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({
            "index": db.index,
            "texts": [doc.page_content for doc in chunks],
            "metadatas": [doc.metadata for doc in chunks]
        }, f)
    # print(f"Indice FAISS salvato correttamente.")
except Exception as e:
    print(f"[ERRORE] durante il salvataggio: {e}")

# === 6. LLM ===
# print("[INFO] Avvio LLM...")
llm = Ollama(model="llama3:instruct", temperature=0)

# === 7. Catena RAG ===
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

# === 8. Esecuzione ===
print(f"\nDomanda: {QUERY}\n")
res = qa_chain.invoke(QUERY)

print(f"\nRisposta:\n{res['result']}\n")
print("Fonti:")
for doc in res['source_documents']:
    print(f"→ {doc.metadata.get('source', 'Sconosciuto')}")
