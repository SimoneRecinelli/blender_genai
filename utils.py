import bpy
import bmesh
import subprocess
import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

# === MODELLO SEMANTICO ===
INDEX_PATH = os.path.join(os.path.dirname(__file__), "blender_faiss_index.pkl")
model = SentenceTransformer("all-MiniLM-L6-v2")

with open(INDEX_PATH, "rb") as f:
    data = pickle.load(f)
    index = data["index"]
    texts = data["texts"]
    metadatas = data["metadatas"]

def query_rag(question, top_k=5):
    query_embedding = model.encode([question])
    distances, indices = index.search(query_embedding, top_k)
    results = []

    for i in indices[0]:
        results.append({
            "text": texts[i],
            "source": metadatas[i]["source"]
        })
    return results


def recupera_chunk_simili_faiss(domanda, k=5):
    risultati = query_rag(domanda, top_k=k)
    return "\n\n".join(
        [f"[Fonte: {r['source']}]\n{r['text']}" for r in risultati]
    )


# === CONTESTO CHAT ===

def build_conversational_context(props):
    history_lines = []
    for entry in props.chat_history:
        prefix = "Utente" if entry.sender == 'USER' else "GenAI"
        history_lines.append(f"{prefix}: {entry.message}")
    return "\n".join(history_lines)


# === CONTESTO MESH BLENDER ===

def get_model_context():
    selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not selected_objs:
        return "Nessun oggetto mesh selezionato nella scena."

    context_list = []
    for obj in selected_objs:
        mesh = obj.data
        dimensions = obj.dimensions
        materials = [slot.material.name if slot.material else "Nessuno" for slot in obj.material_slots]
        uv_layers = list(mesh.uv_layers.keys()) or ["Nessuna"]
        modifiers = [m.type for m in obj.modifiers] or ["Nessuno"]
        shading = "Smooth" if any(p.use_smooth for p in mesh.polygons) else "Flat"
        parent_name = obj.parent.name if obj.parent else "Nessuno"

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        num_tris = sum(1 for f in bm.faces if len(f.verts) == 3)
        is_manifold = all(e.is_manifold for e in bm.edges)
        double_verts = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0001)["targetmap"]
        flipped_normals = sum(1 for f in bm.faces if f.normal.z < 0)

        bm.free()

        context = {
            "Nome oggetto": obj.name,
            "Vertici": len(mesh.vertices),
            "Spigoli": len(mesh.edges),
            "Facce": len(mesh.polygons),
            "Triangoli": num_tris,
            "Dimensioni (X,Y,Z)": f"{dimensions.x:.2f}, {dimensions.y:.2f}, {dimensions.z:.2f}",
            "Modificatori": modifiers,
            "Materiali": materials,
            "UV Maps": uv_layers,
            "Shading": shading,
            "Parent": parent_name,
            "Manifold": "Sì" if is_manifold else "No",
            "Vertici doppi (vicini)": len(double_verts),
            "Facce con normali invertite (Z-)": flipped_normals
        }

        summary = "\n".join([f"{k}: {v}" for k, v in context.items()])
        context_list.append(summary)

    header = f"Hai selezionato {len(selected_objs)} oggetto/i. Ecco i dettagli:\n"
    return header + "\n\n".join(context_list)


# === QUERY OLLAMA CON DOCUMENTAZIONE ===

def query_ollama_with_docs(user_question, props=None):
    print("[DEBUG] Esecuzione query_ollama_with_docs")

    model_context = get_model_context()
    chat_history = build_conversational_context(props) if props else ""

    try:
        blender_docs = recupera_chunk_simili_faiss(user_question)
        print("[DEBUG] Chunk documentazione recuperati.")
    except Exception as e:
        blender_docs = "Documentazione non disponibile."
        print("[ERRORE] Recupero documentazione:", str(e))

    prompt = (
        "Answer based **only** on the official Blender documentation provided below.\n"
        "If the answer is not found there, rely on the scene context or say 'I don't know'.\n\n"
        
        "=== Blender Documentation ===\n"
        f"{blender_docs}\n\n"

        "=== Scene Model Context ===\n"
        f"{model_context}\n\n"

        "=== Conversation History ===\n"
        f"{chat_history}\n\n"

        "=== User Question ===\n"
        f"{user_question}\n\n"

        "Answer in English."
    )

    try:
        result = subprocess.run(
            ["/usr/local/bin/ollama", "run", "llama3.2-vision"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[Errore Ollama] {e.stderr}"
    except Exception as e:
        return f"[Errore generico] {str(e)}"
