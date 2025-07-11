import os
import pickle
import threading
import base64
import requests
import json

# === Import condizionato per Blender ===
try:
    import bpy
    import bmesh
    BLENDER_ENV = True
except ImportError:
    bpy = None
    bmesh = None
    BLENDER_ENV = False

# === CRONOLOGIA CHAT IN MEMORIA E SU DISCO ===

global_chat_history = []

def get_chat_history_path():
    return os.path.join(os.path.dirname(__file__), "chat_history.json")

def add_to_chat_history(sender, message):
    global_chat_history.append({"sender": sender, "message": message})
    save_chat_to_file()

def build_conversational_context_from_json(history_list):
    lines = []
    for entry in history_list:
        prefix = "Utente" if entry["sender"] == 'USER' else "GenAI"
        lines.append(f"{prefix}: {entry['message']}")
    return "\n".join(lines)

def save_chat_to_file(path=None):
    if path is None:
        path = get_chat_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(global_chat_history, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Chat salvata in: {path}")
    except Exception as e:
        print(f"[ERRORE] Salvataggio chat: {e}")

def load_chat_from_file(path=None):
    global global_chat_history
    if path is None:
        path = get_chat_history_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                global_chat_history = json.load(f)
            print(f"[DEBUG] Chat caricata da: {path}")
        except Exception as e:
            print(f"[ERRORE] Caricamento chat: {e}")

'''
def reset_chat_history():
    global global_chat_history
    global_chat_history = []
    path = get_chat_history_path()

    # Sicurezza extra: elimina solo file .json previsti
    if not path.endswith("chat_history.json"):
        print(f"[ERRORE] Tentativo di eliminare un file non valido: {path}")
        return

    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"[DEBUG] Chat history rimossa: {path}")
    except Exception as e:
        print(f"[ERRORE] Impossibile rimuovere la chat history: {e}")
    
    save_chat_to_file()  # forza il salvataggio del JSON vuoto
'''

def reset_chat_history():
    global global_chat_history

    print("[DEBUG] Reset chat history in memoria e su disco")

    # 1. Azzeramento effettivo
    global_chat_history.clear()

    # 2. Sovrascrivi il file con una lista vuota
    try:
        with open(get_chat_history_path(), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Chat JSON sovrascritto vuoto: {get_chat_history_path()}")
    except Exception as e:
        print(f"[ERRORE] Sovrascrittura chat vuota fallita: {e}")


# Carica la chat appena si importa il modulo
load_chat_from_file()

# === QUERY RAG (senza import globali) ===

def query_rag(question, top_k=5):
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return [{"text": "Dipendenze non installate. Premi 'Installa Dipendenze' dal pannello.", "source": "Sistema"}]

    INDEX_PATH = os.path.join(os.path.dirname(__file__), "blender_faiss_index.pkl")

    if not os.path.exists(INDEX_PATH):
        return [{"text": "Indice documentazione non trovato.", "source": "Sistema"}]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)
        index = data["index"]
        texts = data["texts"]
        metadatas = data["metadatas"]

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

# === CONTESTO MESH BLENDER ===

def get_model_context(selected_objs):
    if not BLENDER_ENV:
        return "Context not available outside Blender."

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

# === INVIO HTTP A OLLAMA VISION ===

def send_vision_prompt_to_ollama(prompt: str, image_path: str = None, model: str = "llama3.2-vision") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "num_predict": 300
        }
    }

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload["images"] = [image_b64]

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=False)
        response.raise_for_status()
        output = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                output += data.get("response", "")
        return output.strip()
    except Exception as e:
        return f"[Errore Ollama Vision] {str(e)}"

# === QUERY OLLAMA CON DOC + IMMAGINE (ASYNC) ===

def query_ollama_with_docs_async(user_question, props, selected_objects, update_callback=None):
    def worker():
        print("[DEBUG] Esecuzione async query_ollama_with_docs")

        image_path = props.genai_image_path if props and props.genai_image_path else None
        model_context = get_model_context(selected_objects)
        chat_history = build_conversational_context_from_json(global_chat_history)

        try:
            blender_docs = recupera_chunk_simili_faiss(user_question)
            print("[DEBUG] Chunk documentazione recuperati.")
        except Exception as e:
            blender_docs = "Documentazione non disponibile."
            print("[ERRORE] Recupero documentazione:", str(e))

        if image_path and os.path.exists(image_path):
            prompt = (
                f"You are a visual assistant integrated into Blender.\n"
                f"The user uploaded an image of the 3D scene and asked: '{user_question}'.\n\n"
                "You must analyze the image attentively and respond accordingly.\n"
                "- If the image contains objects, describe their shape, position, lighting, and materials.\n"
                "- If the question refers to a specific object or detail in the image, focus on that.\n"
                "- If no meaningful visual information is found, say: 'The image does not contain enough information.'\n\n"
                "Respond in the same language used in the user's question. Be clear, technical, and structured."
            )

        else:
            prompt = (
                "You are a helpful assistant for Blender 4.4 integrated in a modeling environment.\n"
                "You must analyze each question and act accordingly:\n\n"
                "1. If the question is related to Blender's functionality (modeling, shading, scripting, etc.), "
                "you must answer strictly and exclusively using the official Blender 4.4 documentation and the current scene context.\n"
                "2. If the question is casual, conversational or not technical (e.g., greetings like 'hello', or informal messages), "
                "respond in a friendly and brief way, without using any documentation.\n"
                "3. If the answer is not explicitly supported by the documentation, and the question is technical, respond with: 'not present in the documentation'.\n\n"
                "=== Scene Model Context ===\n"
                f"{model_context}\n\n"
                "=== Blender 4.4 Official Documentation ===\n"
                f"{blender_docs}\n\n"
                "=== Conversation History ===\n"
                f"{chat_history}\n\n"
                "=== User Question ===\n"
                f"{user_question}\n\n"
                "Respond using the same language as the user's question. Keep a clear and technical tone when the question is technical. "
                "Otherwise, be concise and friendly."
            )

        risposta = send_vision_prompt_to_ollama(prompt, image_path)

        def update():
            props.genai_response_text = risposta
            add_to_chat_history("GenAI", risposta)
            if update_callback:
                update_callback()

        if BLENDER_ENV:
            bpy.app.timers.register(update)
        else:
            update()

    add_to_chat_history("USER", user_question)
    threading.Thread(target=worker).start()
