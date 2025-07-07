import os
import pickle
import sys

# Controllo dipendenze esterne
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    from bs4 import BeautifulSoup
except ImportError as e:
    print("Errore: modulo mancante.")
    print("Risoluzione: esegui questo comando per installare le dipendenze:")
    print("   pip install faiss-cpu sentence-transformers bs4")
    sys.exit(1)

# === CONFIGURAZIONE ===
HTML_FOLDER = "/Users/diegosantarelli/Desktop/blender_genai/blender_manual_v440_en"
INDEX_PATH = "blender_faiss_index.pkl"
CHUNK_SIZE = 500

# Modello di embedding ad alte prestazioni per semantic search
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

        for tag in soup(["nav", "header", "footer", "script", "style", "noscript", "form", "aside"]):
            tag.decompose()

        section_divs = soup.find_all("div", class_="section")
        all_text = ""
        for div in section_divs:
            text = div.get_text(separator=" ", strip=True)
            if "Contents Menu Expand" in text or "Toggle Light" in text:
                continue
            all_text += text + "\n"

        if all_text.strip():
            return all_text.strip()

        body = soup.find("body")
        if body:
            body_text = body.get_text(separator=" ", strip=True)
            if "Contents Menu Expand" in body_text:
                lines = body_text.splitlines()
                lines = [l for l in lines if not l.startswith("Contents Menu")]
                return "\n".join(lines)
            return body_text

        return ""

def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

texts = []
metadatas = []
html_file_count = 0

# Estrazione da HTML e suddivisione in chunk
for root, dirs, files in os.walk(HTML_FOLDER):
    if root == HTML_FOLDER:
        continue  # ignora file della root
    for file in files:
        if file.endswith(".html"):
            html_file_count += 1
            path = os.path.join(root, file)
            text = extract_text_from_html(path)
            if len(text.strip()) == 0:
                continue
            chunks = chunk_text(text)
            for chunk in chunks:
                # Prompt tuning: "passage: " per ogni chunk
                texts.append("passage: " + chunk)
                metadatas.append({"source": path})

print(f"File HTML letti: {html_file_count}")
print(f"Chunk generati: {len(texts)}")

if not texts:
    print("ERRORE: Nessun testo trovato. Controlla il path in HTML_FOLDER.")
    exit(1)

# Calcolo embedding (con normalizzazione per cosine similarity)
print("Calcolo degli embeddings...")
embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

# Costruzione indice FAISS con cosine similarity
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)  # IP = Inner Product, usato per cosine similarity normalizzata
index.add(embeddings)

# Salvataggio
with open(INDEX_PATH, "wb") as f:
    pickle.dump({"index": index, "texts": texts, "metadatas": metadatas}, f)

print(f"Indice FAISS salvato in {INDEX_PATH}")
