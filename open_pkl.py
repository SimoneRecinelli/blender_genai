import pickle
import os

# Percorso del file .pkl
index_path = os.path.join(os.path.dirname(__file__), "blender_faiss_index.pkl")

# Carica il file
with open(index_path, "rb") as f:
    data = pickle.load(f)

texts = data["texts"]
metadatas = data["metadatas"]

# Lista degli ID attesi (puoi estenderla a piacere)
expected_ids = {
    "01_000", "01_001", "01_002", "01_003",
    "02_004", "02_005", "02_006", "02_007",
    "03_010", "03_011", "03_012", "03_013",
    "14_057"  # ad esempio
}

print("🔍 Verifica chunk con ID attesi:\n")
found_ids = set()

for i, (text, meta) in enumerate(zip(texts, metadatas)):
    chunk_id = meta.get("id")
    if chunk_id in expected_ids:
        found_ids.add(chunk_id)
        print(f"[{i}] ✅ ID: {chunk_id}")
        print(f"     Topic: {meta.get('topic')}")
        print(f"     Preview: {text.strip().replace('\n', ' ')[:80]}...\n")

# Report finale
missing = expected_ids - found_ids
if missing:
    print("❌ ID mancanti nel .pkl:")
    for mid in sorted(missing):
        print(f"   - {mid}")
else:
    print("✅ Tutti gli ID previsti sono presenti nel file .pkl.")
