import pickle
import os

# Percorso del file .pkl
index_path = os.path.join(os.path.dirname(__file__), "blender_faiss_index.pkl")

# Carica il file
with open(index_path, "rb") as f:
    data = pickle.load(f)

# Estrai i metadati
texts = data["texts"]
metadatas = data["metadatas"]

# Mostra i primi 10 chunk con source
print("🔍 Verifica dei primi chunk:\n")
for i, (text, meta) in enumerate(zip(texts, metadatas[:10])):
    print(f"[{i}] Source:", meta.get("source"))
    preview = text.strip().replace("\n", " ")[:80]
    print(f"     → {preview}...\n")
