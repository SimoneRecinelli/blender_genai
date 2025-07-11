import os
import sys
import pickle

# Aggiunge path pacchetti user
user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

# === Controllo dipendenze ===
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import fitz  # PyMuPDF
except ImportError:
    print("Errore: modulo mancante.")
    print("Risoluzione: assicurati che le dipendenze siano installate dal server Flask.")
    sys.exit(1)

# === Config ===
CHUNK_SIZE = 500
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "Blender_doc.pdf")
INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")

model = SentenceTransformer("intfloat/multilingual-e5-large")

# === Estrazione e chunking ===
def extract_chunks_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text()

    if not all_text.strip():
        return [], []

    words = all_text.split()
    chunks = [" ".join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), CHUNK_SIZE)]
    metadatas = [{"source": f"page_range_{i}"} for i in range(len(chunks))]
    return chunks, metadatas

# === Avvio ===
if not os.path.isfile(PDF_PATH):
    print(f"ERRORE: PDF non trovato in {PDF_PATH}")
    sys.exit(1)

print(f"[INFO] Parsing PDF da: {PDF_PATH}")
texts, metadatas = extract_chunks_from_pdf(PDF_PATH)

if not texts:
    print("ERRORE: Nessun testo estratto.")
    sys.exit(1)

print(f"[INFO] Chunk generati: {len(texts)}")
print("[INFO] Calcolo degli embeddings...")

embeddings = model.encode(texts, show_progress_bar=True)

print("[INFO] Costruzione indice FAISS...")
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

print(f"[DEBUG] Salvataggio in: {INDEX_PATH}")


try:
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"index": index, "texts": texts, "metadatas": metadatas}, f)
    print(f"Indice FAISS salvato in: {INDEX_PATH}")
except Exception as e:
    print(f"ERRORE durante il salvataggio del file: {e}")
