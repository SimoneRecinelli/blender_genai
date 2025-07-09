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
    print("   pip install faiss-cpu sentence-transformers bs4 requests PyQt5 flask psutil")
    sys.exit(1)


# CAMBIA QUESTO PATH in base a dove hai salvato la cartella HTML
HTML_FOLDER = "/Users/diegosantarelli/Desktop/blender_genai/blender_manual_v440_en"
INDEX_PATH = "blender_faiss_index.pkl"
CHUNK_SIZE = 500

model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_html(file_path):

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

        # Rimuovi script e roba ovvia
        for tag in soup(["nav", "header", "footer", "script", "style", "noscript", "form", "aside"]):
            tag.decompose()

        # Trova il div centrale, di solito è il primo <div class="section"> significativo
        section_divs = soup.find_all("div", class_="section")

        all_text = ""
        for div in section_divs:
            text = div.get_text(separator=" ", strip=True)
            # ignora blocchi tipo "Contents Menu Expand Light mode..."
            if "Contents Menu Expand" in text or "Toggle Light" in text:
                continue
            all_text += text + "\n"

        if all_text.strip():
            return all_text.strip()

        # Fallback finale sul body, ma attenzione: con filtro extra
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

# 🔍 Estrai e chunkizza
for root, dirs, files in os.walk(HTML_FOLDER):
    # ignora i file della root
    if root == HTML_FOLDER:
        continue
    for file in files:
        if file.endswith(".html"):
            html_file_count += 1
            path = os.path.join(root, file)
            text = extract_text_from_html(path)
            if len(text.strip()) == 0:
                continue
            chunks = chunk_text(text)
            for chunk in chunks:
                texts.append(chunk)
                metadatas.append({"source": path})

print(f"File HTML letti: {html_file_count}")
print(f"Chunk generati: {len(texts)}")

if not texts:
    print("ERRORE: Nessun testo trovato. Controlla il path in HTML_FOLDER.")
    exit(1)

# Calcolo embedding
print("Calcolo degli embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)

# Costruzione indice FAISS
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# Salvataggio
with open(INDEX_PATH, "wb") as f:
    pickle.dump({"index": index, "texts": texts, "metadatas": metadatas}, f)

print(f"Indice FAISS salvato in {INDEX_PATH}")
