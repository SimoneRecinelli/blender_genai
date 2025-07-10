import pickle

# Percorso al file pickle
INDEX_PATH = "/Users/diegosantarelli/Desktop/blender_genai/blender_faiss_index.pkl"

with open(INDEX_PATH, "rb") as f:
    data = pickle.load(f)

texts = data["texts"]
metadatas = data["metadatas"]

# Parametri da personalizzare
start = 1000  # chunk di partenza (0-based)
count = 3   # quanti chunk successivi mostrare

for i in range(start, start + count):
    print(f"\n=== CHUNK {i+1} ===")
    print("Fonte:", metadatas[i].get("source", "sconosciuta"))
    print("Lunghezza:", len(texts[i]))
    print("Testo (primi 500 caratteri):")
    print(texts[i][:500].replace("\n", " "))
