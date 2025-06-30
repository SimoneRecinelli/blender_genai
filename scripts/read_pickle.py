import pickle

# Percorso al file pickle
INDEX_PATH = "/Users/diegosantarelli/Desktop/blender_genai/blender_faiss_index.pkl"

# Caricamento del contenuto
with open(INDEX_PATH, "rb") as f:
    data = pickle.load(f)

# Esplora cosa contiene
index = data["index"]         # oggetto FAISS
texts = data["texts"]         # lista di chunk di testo
metadatas = data["metadatas"] # lista di dizionari con info (es. 'source')

# Visualizza primi 3 chunk
for i in range(3):
    print(f"\n=== CHUNK {i+1} ===")
    print("Fonte:", metadatas[i]["source"])
    print("Testo:", texts[i][500:1000])  # primi 500 caratteri per leggibilità
