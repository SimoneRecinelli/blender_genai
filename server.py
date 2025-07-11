import sys
import os
import subprocess
import platform
import threading
import socket

# === 1. Aggiungi ~/.local/lib/... a sys.path (pacchetti --user) ===
user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

# === 2. Abilita pip se non esiste (necessario in Blender vanilla) ===
try:
    import pip
except ImportError:
    print("[SETUP] pip non trovato. Attivazione con ensurepip...")
    subprocess.call([sys.executable, "-m", "ensurepip"])

# === 3. Installa le dipendenze mancanti ===
def install_dependencies_if_needed():
    required = [
        "faiss-cpu",
        "sentence-transformers",
        "flask",
        "requests",
        "PyQt5",
        "psutil",
        "PyMuPDF",
        "langchain",
        "langchain-community",
        "pyobjc"
    ]

    for package in required:
        if package == "pyobjc" and platform.system() != "Darwin":
            continue  # PyObjC solo su macOS

        try:
            mod = package.replace("-", "_").split(".")[0]
            if mod == "faiss_cpu":
                __import__("faiss")
            else:
                __import__(mod)
        except ImportError:
            print(f"[SETUP] Installazione mancante: {package}")
            subprocess.call([sys.executable, "-m", "pip", "install", "--user", package])

install_dependencies_if_needed()

# === 4. Ora puoi importare Flask e il resto in sicurezza ===
from flask import Flask, request, jsonify
import bpy
from .utils import query_ollama_with_docs_async

# === 5. Avvio server Flask ===
app = Flask(__name__)
last_response = {"text": "", "ready": False}

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    domanda = data.get('question', '')
    image_path = data.get('image_path', '')

    # Reset della risposta
    last_response["text"] = ""
    last_response["ready"] = False

    def update_callback(props):
        print("[Flask] ✅ Risposta generata da Ollama!")
        last_response["text"] = props.genai_response_text
        last_response["ready"] = True

    def run_in_main_thread():
        try:
            props = bpy.context.scene.genai_props
            props.genai_question = domanda
            props.genai_image_path = image_path

            selected_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
            query_ollama_with_docs_async(domanda, props, selected_objects, lambda: update_callback(props))
        except Exception as e:
            print("[ERRORE] Nel thread principale:", str(e))

    bpy.app.timers.register(run_in_main_thread)

    return jsonify({"status": "Domanda ricevuta da Blender"})

@app.route('/response', methods=['GET'])
def get_response():
    if last_response["ready"]:
        return jsonify({
            "status": "ready",
            "response": last_response["text"]
        })
    else:
        return jsonify({
            "status": "waiting"
        })

_flask_server_started = False

def start_flask_server():
    global _flask_server_started
    if not _flask_server_started:
        print("[DEBUG] Server Flask avviato su http://127.0.0.1:5000")
        threading.Thread(
            target=lambda: app.run(host="127.0.0.1", port=5000),
            daemon=True
        ).start()
        _flask_server_started = True
    else:
        print("[DEBUG] Server Flask già avviato.")
