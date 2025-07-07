"""
import bpy
import bmesh
import subprocess
import os
import pickle
import faiss
import threading
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

def get_model_context(selected_objs):
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

# === QUERY OLLAMA CON DOCUMENTAZIONE (NON BLOCCANTE) ===

def query_ollama_with_docs_async(user_question, props, selected_objects, update_callback=None):
    def worker():
        print("[DEBUG] Esecuzione async query_ollama_with_docs")

        model_context = get_model_context(selected_objects)
        chat_history = build_conversational_context(props) if props else ""

        try:
            blender_docs = recupera_chunk_simili_faiss(user_question)
            print("[DEBUG] Chunk documentazione recuperati.")
        except Exception as e:
            blender_docs = "Documentazione non disponibile."
            print("[ERRORE] Recupero documentazione:", str(e))

        prompt = (
            "You are a helpful assistant for Blender 4.4.\n\n"
            "Answer based **strictly and exclusively** on the official Blender 4.4 documentation provided below.\n"
            "Do not include any information from unofficial sources, online forums, previous versions of Blender, or general knowledge.\n"
            "If the answer is not explicitly covered in the documentation, respond with: 'not present in the documentation'.\n\n"
            "In your response, also take into account the following detailed description of the selected object(s) in the Blender scene.\n"
            "Include as many specific details as possible about each selected object, such as geometry, materials, modifiers, shading, UV maps, and parent relationships.\n\n"

            "=== Scene Model Context ===\n"
            f"{model_context}\n\n"

            "=== Blender 4.4 Official Documentation ===\n"
            f"{blender_docs}\n\n"

            "=== Conversation History ===\n"
            f"{chat_history}\n\n"

            "=== User Question ===\n"
            f"{user_question}\n\n"

            "Respond in clear and technical English."
        )


        try:
            result = subprocess.run(
                ["/usr/local/bin/ollama", "run", "llama3.2-vision"],
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
            risposta = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            risposta = f"[Errore Ollama] {e.stderr}"
        except Exception as e:
            risposta = f"[Errore generico] {str(e)}"

        def update():
            props.genai_response_text = risposta
            if update_callback:
                update_callback()

        bpy.app.timers.register(update)

    threading.Thread(target=worker).start()

    


import bpy
import bmesh
import subprocess
import os
import pickle
import faiss
import threading
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

def get_model_context(selected_objs):
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

# === QUERY OLLAMA CON DOCUMENTAZIONE (NON BLOCCANTE) ===

def query_ollama_with_docs_async(user_question, props, selected_objects, update_callback=None):
    def worker():
        print("[DEBUG] Esecuzione async query_ollama_with_docs")

        model_context = get_model_context(selected_objects)
        chat_history = build_conversational_context(props) if props else ""

        try:
            blender_docs = recupera_chunk_simili_faiss(user_question)
            print("[DEBUG] Chunk documentazione recuperati.")
        except Exception as e:
            blender_docs = "Documentazione non disponibile."
            print("[ERRORE] Recupero documentazione:", str(e))

        prompt = (
            "You are a helpful assistant for Blender 4.4.\n\n"
            "Answer based **strictly and exclusively** on the official Blender 4.4 documentation provided below.\n"
            "Do not include any information from unofficial sources, online forums, previous versions of Blender, or general knowledge.\n"
            "If the answer is not explicitly covered in the documentation, respond with: 'not present in the documentation'.\n\n"
            "In your response, also take into account the following detailed description of the selected object(s) in the Blender scene.\n"
            "Include as many specific details as possible about each selected object, such as geometry, materials, modifiers, shading, UV maps, and parent relationships.\n\n"

            "=== Scene Model Context ===\n"
            f"{model_context}\n\n"

            "=== Blender 4.4 Official Documentation ===\n"
            f"{blender_docs}\n\n"

            "=== Conversation History ===\n"
            f"{chat_history}\n\n"

            "=== User Question ===\n"
            f"{user_question}\n\n"

            "Respond in clear and technical English."
        )

        image_path = props.genai_image_path if props and props.genai_image_path else None
        command = ["/usr/local/bin/ollama", "run", "llama3.2-vision"]
        if image_path and os.path.exists(image_path):
            command += ["--image", image_path]

        try:
            result = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
            risposta = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            risposta = f"[Errore Ollama] {e.stderr}"
        except Exception as e:
            risposta = f"[Errore generico] {str(e)}"

        def update():
            props.genai_response_text = risposta
            if update_callback:
                update_callback()

        bpy.app.timers.register(update)

    threading.Thread(target=worker).start()

    
"""

import bpy
import bmesh
import os
import pickle
import faiss
import threading
import base64
import requests
import json
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

def get_model_context(selected_objs):
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

def send_vision_prompt_to_ollama(prompt: str, image_path: str = None, model: str = "llava:7b") -> str:
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

        model_context = get_model_context(selected_objects)
        chat_history = build_conversational_context(props) if props else ""

        try:
            blender_docs = recupera_chunk_simili_faiss(user_question)
            print("[DEBUG] Chunk documentazione recuperati.")
        except Exception as e:
            blender_docs = "Documentazione non disponibile."
            print("[ERRORE] Recupero documentazione:", str(e))

        prompt = (
            "You are a helpful assistant for Blender 4.4.\n\n"
            "You must answer the user's question strictly and exclusively based on the official Blender 4.4 documentation **and** the description of the selected objects in the scene.\n"
            "Do not use external knowledge, online forums, prior Blender versions, or generic reasoning.\n"
            "If the answer is not explicitly supported by the documentation, respond with: 'not present in the documentation'.\n\n"

            "=== Scene Model Context ===\n"
            f"{model_context}\n\n"
            "=== Blender 4.4 Official Documentation ===\n"
            f"{blender_docs}\n\n"
            "=== Conversation History ===\n"
            f"{chat_history}\n\n"
            "=== User Question ===\n"
            f"{user_question}\n\n"
            "Respond using the same language as the user's question, with a clear and technical tone."
        )

        image_path = props.genai_image_path if props and props.genai_image_path else None
        risposta = send_vision_prompt_to_ollama(prompt, image_path)

        def update():
            props.genai_response_text = risposta
            if update_callback:
                update_callback()

        bpy.app.timers.register(update)

    threading.Thread(target=worker).start()
