import os
import sys
import platform
import pickle

# === Aggiunge la cartella modules di Blender al sys.path ===
def get_modules_dir():
    blender_version = "4.5"  # cambia se usi Blender diverso
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Application Support/Blender/{blender_version}/scripts/modules")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), f"Blender Foundation\\Blender\\{blender_version}\\scripts\\modules")
    else:
        return os.path.expanduser(f"~/.config/blender/{blender_version}/scripts/modules")

modules_dir = get_modules_dir()
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


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
QUERY = "How I can apply a texture in Blender?"

# === 1. Caricamento PDF ===
loader = PyMuPDFLoader(PDF_PATH)
docs = loader.load()

# === 2. Suddivisione in chunk ===
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# 👉 Aggiungo info extra per i metadati
for i, doc in enumerate(chunks):
    page = doc.metadata.get("page", "unknown")
    doc.metadata["chunk_index"] = i
    doc.metadata["ref"] = f"pagina {page}, chunk {i}"

# === 3. Embedding model ===
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# === 4. Costruzione FAISS retriever ===
db = FAISS.from_documents(chunks, embeddings)
retriever = db.as_retriever(search_kwargs={"k": 6})

# === 💾 5. Salvataggio su disco ===
try:
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({
            "index": db.index,
            "texts": [doc.page_content for doc in chunks],
            "metadatas": [doc.metadata for doc in chunks]
        }, f)
except Exception as e:
    print(f"[ERRORE] durante il salvataggio: {e}")

# === 6. LLM ===
llm = Ollama(model="llama3:instruct", temperature=0)

# === 7. Catena RAG ===
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

# === 8. Esecuzione ===
print(f"\nDomanda: {QUERY}\n")
res = qa_chain.invoke(QUERY)

print(f"\nRisposta:\n{res['result']}\n")
print("Fonti:")
for doc in res['source_documents']:
    source = doc.metadata.get('source', 'Sconosciuto')
    ref = doc.metadata.get('ref', '')
    print(f"→ {source} {ref}")
