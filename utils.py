import os
import pickle
import threading
import base64
import requests
import json

try:
    import bpy
    import bmesh
    BLENDER_ENV = True
except ImportError:
    bpy = None
    bmesh = None
    BLENDER_ENV = False

# GPU Detection
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
    banal = {"hello", "hey", "ok", "how are you", "good morning", "good evening"}
    if question in banal:
        return False
    if len(question.split()) < 3:
        return False
    return True


# GESTIONE CRONOLOGIA CHAT

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
            except Exception as e:
                print(f"[ERRORE] Caricamento chat: {e}")
        else:
            self._history = []

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
            os.chmod(self._path, 0o644)
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

# QUERY RAG

def query_rag(question, top_k=5):
    import faiss
    from sentence_transformers import SentenceTransformer

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")

    if not os.path.exists(INDEX_PATH):
        return [{"text": "Indice documentazione non trovato.", "source": "Sistema"}]

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
        meta = metadatas[i]
        chapter = meta.get("chapter")
        topic = meta.get("topic")
        if chapter and topic:
            source = f"{chapter} - {topic}"
        elif meta.get("source"):
            source = meta["source"]
        else:
            source = "Fonte sconosciuta"

        results.append({
            "text": texts[i],
            "source": source
        })

    return results


def recupera_chunk_simili_faiss(domanda, k=15):
    import faiss
    from sentence_transformers import SentenceTransformer

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INDEX_PATH = os.path.join(BASE_DIR, "blender_faiss_index.pkl")

    if not os.path.exists(INDEX_PATH):
        return "[ERRORE] Indice FAISS non trovato."

    model = SentenceTransformer("intfloat/e5-large-v2", device=get_device_for_transformer())

    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)
        index = data["index"]
        texts = data["texts"]
        metadatas = data["metadatas"]

    query_embedding = model.encode([domanda])
    distances, faiss_indices = index.search(query_embedding, k)

    risultati = []
    for idx in faiss_indices[0]:
        testo = texts[idx]
        meta = metadatas[idx]

        chapter = meta.get("chapter")
        topic = meta.get("topic")

        if chapter and topic:
            fonte = f"{chapter} - {topic}"
        elif meta.get("source"):
            fonte = meta["source"]
        else:
            fonte = "Fonte sconosciuta"

        risultati.append(f"[Fonte: {fonte}]\n{testo}")

    return "\n\n".join(risultati)

def get_model_context(selected_objs):
    if not BLENDER_ENV:
        return "Context not available outside Blender."

    if not selected_objs:
        return "Nessun oggetto selezionato nella scena."

    context_list = []
    type_counts = {}
    names_by_type = {}

    for obj in selected_objs:
        obj_type = obj.type
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        names_by_type.setdefault(obj_type, []).append(obj.name)

        # MESH
        if obj_type == 'MESH':
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

        # LIGHT
        elif obj_type == 'LIGHT':
            light = obj.data
            context = {
                "Nome oggetto": obj.name,
                "Tipo": obj_type,
                "Parent": obj.parent.name if obj.parent else "Nessuno",
                "Posizione": f"{obj.location.x:.2f}, {obj.location.y:.2f}, {obj.location.z:.2f}",
                "Tipo luce": light.type,
                "Energia": f"{light.energy}",
                "Colore": f"({light.color[0]:.2f}, {light.color[1]:.2f}, {light.color[2]:.2f})",
                "Shadows": "On" if light.use_shadow else "Off"
            }

        # CAMERA
        elif obj_type == 'CAMERA':
            cam = obj.data
            context = {
                "Nome oggetto": obj.name,
                "Tipo": obj_type,
                "Parent": obj.parent.name if obj.parent else "Nessuno",
                "Posizione": f"{obj.location.x:.2f}, {obj.location.y:.2f}, {obj.location.z:.2f}",
                "Tipo proiezione": cam.type,  # 'PERSP', 'ORTHO', 'PANO'
                "Lunghezza focale (mm)": f"{cam.lens:.2f}" if cam.type == "PERSP" else "N/A",
                "Clip Start": f"{cam.clip_start:.3f}",
                "Clip End": f"{cam.clip_end:.1f}",
                "Sensor Width (mm)": f"{cam.sensor_width:.2f}",
                "Depth of Field": "On" if cam.dof.use_dof else "Off"
            }

        # ALTRI TIPI
        else:
            context = {
                "Nome oggetto": obj.name,
                "Tipo": obj_type,
                "Parent": obj.parent.name if obj.parent else "Nessuno",
                "Posizione": f"{obj.location.x:.2f}, {obj.location.y:.2f}, {obj.location.z:.2f}",
                "Rotazione (XYZ°)": f"{obj.rotation_euler.x:.1f}, {obj.rotation_euler.y:.1f}, {obj.rotation_euler.z:.1f}",
                "Scala": f"{obj.scale.x:.2f}, {obj.scale.y:.2f}, {obj.scale.z:.2f}",
            }

            if obj.data and hasattr(obj.data, "name"):
                context["Datablock"] = obj.data.name

            if hasattr(obj, "dimensions"):
                context[
                    "Dimensioni (X,Y,Z)"] = f"{obj.dimensions.x:.2f}, {obj.dimensions.y:.2f}, {obj.dimensions.z:.2f}"

        summary = "\n".join([f"{k}: {v}" for k, v in context.items()])
        context_list.append(summary)

    type_summary = []
    for obj_type, count in type_counts.items():
        names = ", ".join(names_by_type[obj_type])
        type_summary.append(f"{count} {obj_type}{'s' if count > 1 else ''} ({names})")

    header = f"The scene you have selected contains {len(selected_objs)} object(s): " + " – ".join(type_summary) + ".\n\n"
    return header + "\n\n".join(context_list)




# INVIO HTTP A OLLAMA VISION 

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


# QUERY OLLAMA CON DOC + IMMAGINE (ASYNC)

def query_ollama_with_docs_async(user_question, props, selected_objects, update_callback=None):

    def worker():
        print("⭐️⭐️ ------------------ Esecuzione query ------------------ ⭐️⭐")

        image_path = props.genai_image_path if props and getattr(props, 'genai_image_path', None) else None
        current_selection = selected_objects
        model_context = get_model_context(current_selection)

        history_manager = ChatHistoryManager()
        history_manager.load()

        # Storico: aggiungo la domanda dell'utente se presente
        if user_question.strip():
            history_manager.add("USER", user_question)

        chat_history = history_manager.get_conversational_context()

        # Recupero documentazione solo per domande tecniche
        blender_docs = ""
        if is_question_technical(user_question):
            try:
                print(f"[DEBUG] Domanda tecnica rilevata: {user_question}")
                blender_docs = recupera_chunk_simili_faiss(user_question, k=10)
            except Exception as e:
                print(f"[ERROR] Documentation retrieval failed: {str(e)}")
                blender_docs = "[ERRORE] Documentazione non disponibile."
        else:
            print("[DEBUG] Domanda non tecnica — nessun chunk documentazione usato.")
            blender_docs = ""

        # PROMPT BUILDER
        def build_prompt(user_question: str, scene_context: str, doc_text: str, chat_history: str) -> str:
            return (
                "You are a strict technical assistant for Blender 4.4.\n"
                "Your ONLY allowed knowledge is what is explicitly stated in the documentation below.\n\n"
                "🚫 Do NOT use general knowledge or external assumptions.\n"
                "✅ You MUST base your answer exclusively on the documentation provided.\n"
                "💡 If the documentation contains relevant explanations, instructions, keybindings, or descriptions "
                "(even if scattered across different sections), you MUST synthesize and integrate them to answer the question.\n"
                "If the question is a greeting (such as hello and similiars) or compliments or any other option instead of a formal question about Blender, reply politely.\n"
                "If the user asks a question about the scene:\n"
                "- Regardless of object type, if the Scene Model Context below contains any objects, you MUST describe them in detail.\n"
                "- If truly no object is selected and no screenshot is provided, politely ask the user to select an object or provide a screenshot.\n"

                "=== Scene Model Context ===\n"
                f"{scene_context}\n\n"
                "=== Blender 4.4 Official Documentation ===\n"
                f"{doc_text}\n\n"
                "=== Conversation History ===\n"
                f"{chat_history}\n\n"
                "=== User Question ===\n"
                f"{user_question}\n\n"
                "Respond only in English. Keep a professional, technical tone. Answer only if the documentation allows it."
            )

        def build_image_prompt(user_question: str, scene_context: str, chat_history: str) -> str:
            """
            Costruisce un prompt specifico per quando è presente uno screenshot della scena Blender.
            """
            return (
                "You are a visual assistant integrated into Blender.\n"
                "You are given a screenshot of the 3D scene in Blender.\n"
                "Analyze only what is visible in the 3D Viewport and related UI panels.\n"
                "Provide a detailed and accurate description without guessing.\n"
                "If the user provides a question, answer it using both the image and the scene context provided.\n"
                "If no question is provided, describe the scene following a technical, factual structure:\n"
                "- Viewport state (perspective/orthographic, grid visibility)\n"
                "- List of visible objects with type and selection state\n"
                "- Active object details if visible\n"
                "- Camera and lights presence and placement\n"
                "- Shading/overlays state if visible\n"
                "- Short summary of the scene\n\n"
                f"=== Scene Model Context (from Blender selection) ===\n{scene_context}\n\n"
                f"=== User Question (optional) ===\n{user_question or 'Describe the scene.'}\n"
            )

        # COSTRUISCI PROMPT
        if image_path and os.path.exists(image_path):
            prompt = build_image_prompt(user_question, model_context, chat_history)
            if user_question.strip():
                prompt += f"=== User Question ===\n{user_question}\n"
        else:
            prompt = build_prompt(user_question, model_context, blender_docs, chat_history)

        print("\n[DEBUG] PROMPT COMPLETO INVIATO A OLLAMA:\n", prompt)

        if image_path:
            print("[DEBUG] ⬆️ Invio immagine a Ollama")
            print(f"         Path: {image_path}")
            print(f"         Esiste? {'✅' if os.path.exists(image_path) else '❌'}")
        else:
            print("[DEBUG] 🚫 Nessuna immagine fornita (image_path=None)")

        risposta = send_vision_prompt_to_ollama(prompt, image_path)

        print("\n[DEBUG] ✅ Risposta:\n", risposta)

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
