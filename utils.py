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

# === GPU Detection (Apple Silicon) ===
def is_gpu_available():
    import platform
    from torch import backends
    return platform.system() == "Darwin" and backends.mps.is_available()

def get_device_for_transformer():
    if is_gpu_available():
        print("[INFO] Uso della GPU Apple MPS abilitato.")
        return "mps"
    print("[INFO] Uso della CPU per sentence-transformers.")
    return "cpu"


def is_question_technical(question: str) -> bool:
    question = question.strip().lower()
    banal = {"ciao", "hello", "hey", "salve", "grazie", "ok", "come va", "how are you", "buongiorno", "good morning",
             "buonasera", "good evening"}
    if question in banal:
        return False
    if len(question.split()) < 3:
        return False
    return True

# === CRONOLOGIA CHAT IN MEMORIA E SU DISCO ===

# === GESTIONE CRONOLOGIA CHAT CON CLASSE ===

def get_chat_history_path():
    return os.path.join(os.path.dirname(__file__), "chat_history.json")


class ChatHistoryManager:
    def __init__(self, path=None):
        self._path = path or get_chat_history_path()
        self._history = []

    def load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
                    print(f"[DEBUG] Chat caricata da: {self._path}")
            except Exception as e:
                print(f"[ERRORE] Caricamento chat: {e}")
        else:
            self._history = []

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
            os.chmod(self._path, 0o644)  # ✅ Assicura lettura/scrittura
            print(f"[DEBUG] Chat salvata in: {self._path}")
        except Exception as e:
            print(f"[ERRORE] Salvataggio chat: {e}")

    def add(self, sender, message):
        self._history.append({"sender": sender, "message": message})
        self.save()

    def reset(self):
        self._history = []
        self.save()
        print(f"[DEBUG] Chat JSON svuotato: {self._path}")

    def get_conversational_context(self):
        lines = []
        for entry in self._history:
            prefix = "Utente" if entry["sender"] == 'USER' else "GenAI"
            lines.append(f"{prefix}: {entry['message']}")
        return "\n".join(lines)

    def get_history_list(self):
        return self._history[:]

# === QUERY RAG (senza import globali) ===

def query_rag(question, top_k=5):
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return [{"text": "Dipendenze non installate. Premi 'Installa Dipendenze' dal pannello.", "source": "Sistema"}]


    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # non salire di livello
    INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")

    if not os.path.exists(INDEX_PATH):
        return [{"text": "Indice documentazione non trovato.", "source": "Sistema"}]

    # model = SentenceTransformer("intfloat/multilingual-e5-large", device=get_device_for_transformer())
    model = SentenceTransformer("intfloat/e5-large-v2", device=get_device_for_transformer())

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
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return "[ERRORE] Moduli mancanti."

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # non salire di livello
    INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")

    if not os.path.exists(INDEX_PATH):
        return "[ERRORE] Indice FAISS non trovato."

    # model = SentenceTransformer("intfloat/multilingual-e5-large")

    # model = SentenceTransformer("intfloat/multilingual-e5-large", device=get_device_for_transformer())

    model = SentenceTransformer("intfloat/e5-large-v2", device=get_device_for_transformer())

    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)
        index = data["index"]
        texts = data["texts"]
        metadatas = data["metadatas"]

    query_embedding = model.encode([domanda])
    distances, faiss_indices = index.search(query_embedding, k)

    print(f"\n[DEBUG] Chunk simili per la domanda: \"{domanda}\"")
    risultati = []
    for idx in faiss_indices[0]:
        testo = texts[idx]
        meta = metadatas[idx]
        fonte = meta.get("source") or f"{meta.get('chapter', '?')} - {meta.get('topic', '?')}"
        preview = testo.strip().replace("\n", " ")[:150]
        print(f" → Chunk FAISS #{idx} [Fonte: {fonte}]: {preview}...")
        risultati.append(f"[Fonte: {fonte}]\n{testo}")

    return "\n\n".join(risultati)

# === CONTESTO MESH BLENDER ===

def get_model_context(selected_objs):
    if not BLENDER_ENV:
        return "Context not available outside Blender."

    if not selected_objs:
        return "Nessun oggetto selezionato nella scena."

    context_list = []
    type_counts = {}
    names_by_type = {}

    for obj in selected_objs:
        # Conta oggetti per tipo
        obj_type = obj.type
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        names_by_type.setdefault(obj_type, []).append(obj.name)

        if obj_type != 'MESH':
            context = {
                "Nome oggetto": obj.name,
                "Tipo": obj_type,
                "Nota": "Questo tipo di oggetto non è supportato per l'analisi geometrica. Seleziona una Mesh per analisi dettagliata."
            }
            summary = "\n".join([f"{k}: {v}" for k, v in context.items()])
            context_list.append(summary)
            continue

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

    # Riepilogo iniziale
    type_summary = []
    for obj_type, count in type_counts.items():
        names = ", ".join(names_by_type[obj_type])
        type_summary.append(f"{count} {obj_type}{'s' if count > 1 else ''} ({names})")

    header = f"The scene you have selected contains {len(selected_objs)} object(s): " + " – ".join(type_summary) + ".\n\n"

    return header + "\n\n".join(context_list)



# === INVIO HTTP A OLLAMA VISION ===

def send_vision_prompt_to_ollama(prompt: str, image_path: str = None, model: str = "llama3.2-vision") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "num_predict": 2048
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
        # model_context = get_model_context(selected_objects)

        # ✅ SELEZIONE È GIÀ PASSATA DAL THREAD PRINCIPALE
        current_selection = selected_objects

        model_context = get_model_context(current_selection)

        history_manager = ChatHistoryManager()
        history_manager.load()

        if user_question.strip():
            history_manager.add("USER", user_question)
        # history_manager.save()
        chat_history = history_manager.get_conversational_context()

        # if is_question_technical(user_question):
        #     try:
        #         blender_docs = recupera_chunk_simili_faiss(user_question)
        #         print("[DEBUG] Chunk documentazione recuperati.")
        #     except Exception as e:
        #         blender_docs = "Documentazione non disponibile."
        #         print("[ERRORE] Recupero documentazione:", str(e))
        # else:
        #     blender_docs = ""
        #     if user_question.strip():
        #         print("[DEBUG] RAG disattivato per domanda non tecnica.")

        if is_question_technical(user_question):
            try:
                blender_docs = recupera_chunk_simili_faiss(user_question)
                if "[ERRORE]" in blender_docs:
                    risposta = "not present in the documentation"
                    print("[ERRORE] Documentazione non trovata, risposta forzata.")
                    history_manager.add("GenAI", risposta)
                    if BLENDER_ENV:
                        bpy.app.timers.register(lambda: setattr(props, "genai_response_text", risposta))
                    else:
                        props.genai_response_text = risposta
                    return  # ⛔ Fermati qui
                print("[DEBUG] Chunk documentazione recuperati.")
            except Exception as e:
                risposta = "not present in the documentation"
                print(f"[ERRORE] Recupero documentazione fallito: {str(e)}")
                history_manager.add("GenAI", risposta)
                if BLENDER_ENV:
                    bpy.app.timers.register(lambda: setattr(props, "genai_response_text", risposta))
                else:
                    props.genai_response_text = risposta
                return
        else:
            blender_docs = ""

        print("[DEBUG] 🔍 Contenuto recuperato dai chunk:\n", blender_docs)

        # === PROMPT VISION o RAG ===
        def build_prompt(user_question: str, scene_context: str, blender_chunks: list[str], chat_history: str) -> str:
            chunked_context = "\n\n".join(f"[Source]\n{chunk.strip()}" for chunk in blender_chunks if chunk.strip())
            return (
                "You are a technical assistant for Blender 4.4 integrated in a modeling environment. "
                "You have NO access to external knowledge or pretraining. Your entire knowledge is LIMITED to the following documentation excerpts. "
                "If the answer to the user question is not DIRECTLY and LITERALLY stated in the documentation section below, respond only with:\n"
                "not present in the documentation.\n\n"
                "You must analyze each question and act accordingly:\n\n"
                "1. If the question is related to Blender's functionality (modeling, shading, scripting, etc.), "
                "you must answer strictly and exclusively using the official Blender 4.4 documentation and the current scene context.\n"
                "2. If the question is casual, conversational or not technical (e.g., greetings like 'hello', or informal messages), "
                "respond in a friendly and brief way, without using any documentation.\n\n"
                "=== Scene Model Context ===\n"
                f"{scene_context}\n\n"
                "=== Blender 4.4 Official Documentation ===\n"
                f"{chunked_context}\n\n"
                "=== Conversation History ===\n"
                f"{chat_history}\n\n"
                "=== User Question ===\n"
                f"{user_question}\n\n"
                "Respond **exclusively** in English, regardless of the user's question language. Use a clear and technical tone when the question is technical. Otherwise, be concise and friendly."
            )

        if image_path and os.path.exists(image_path):
            prompt = (
                "You are a visual assistant integrated into Blender.\n"
                "You are given a screenshot of the 3D scene in Blender.\n"
                "If a question is provided, respond using both the image and question.\n"
                "If no question is provided, just describe what is visible in the image.\n\n"
            )
            if user_question.strip():
                prompt += f"=== User Question ===\n{user_question}\n"
        else:
            chunks = blender_docs.strip().split("\n\n") if blender_docs.strip() else []
            prompt = build_prompt(user_question, model_context, chunks, chat_history)

        if image_path:
            print("[DEBUG] ⬆️ Invio immagine a Ollama")
            print(f"         Path: {image_path}")
            print(f"         Esiste? {'✅' if os.path.exists(image_path) else '❌'}")
        else:
            print("[DEBUG] 🚫 Nessuna immagine fornita (image_path=None)")

        risposta = send_vision_prompt_to_ollama(prompt, image_path)

        def update():
            props.genai_response_text = risposta
            history_manager.add("GenAI", risposta)
            if update_callback:
                update_callback()

        if BLENDER_ENV:
            bpy.app.timers.register(update)
        else:
            update()

    threading.Thread(target=worker).start()
