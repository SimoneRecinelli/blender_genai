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
    "02_004", "02_005", "02_006", "02_007", "02_008", "02_009",
    "03_010", "03_011", "03_012", "03_013", "03_014", "03_015",
    "04_016", "04_017", "04_018", "04_019", "04_020", "04_021",
    "05_022", "05_023", "05_024", "05_025",
    "06_026", "06_027", "06_028", "06_029", "06_030", "06_031",
    "07_032", "07_033", "07_034", "07_035",
    "08_036", "08_037", "08_038", "08_039",
    "09_040", "09_041", "09_042", "09_043",
    "10_044", "10_045", "10_046",
    "11_047", "11_048", "11_049", "11_050",
    "12_051", "12_052", "12_053",
    "13_054", "13_055", "13_056",
    "14_057", "14_058", "14_059",
    "15_060", "15_061",
    "16_062", "16_063", "16_064", "16_065", "16_066", "16_067", "16_068", "16_069", "16_070", "16_071", "16_072",
    "17_073",
    "18_074", "18_075", "18_076", "18_077", "18_078", "18_079", "18_080", "18_081"
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
