import sys
import os
import subprocess
import platform
import threading
import importlib.util

# === 1. Aggiungi la cartella 'scripts/modules' di Blender a sys.path ===
try:
    import bpy
    modules_dir = bpy.utils.user_resource('SCRIPTS', path="modules", create=True)
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
except Exception as e:
    print(f"[ERRORE] Impossibile accedere a bpy o user_resource: {e}")
    modules_dir = None

# === 2. Abilita pip se necessario ===
try:
    import pip
except ImportError:
    print("[SETUP] pip non trovato. Attivazione con ensurepip...")
    subprocess.call([sys.executable, "-m", "ensurepip"])

# === 3. Installa le dipendenze in 'scripts/modules' ===
def is_installed(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False

def install_dependencies_if_needed():
    if not modules_dir:
        print("[ERRORE] 'modules_dir' non disponibile. Interrompo.")
        return

    required = [
        ("faiss-cpu", "faiss"),
        ("sentence-transformers", "sentence_transformers"),
        ("flask", "flask"),
        ("requests", "requests"),
        ("PyQt5", "PyQt5"),
        ("psutil", "psutil"),
        ("PyMuPDF", "fitz"),
        ("langchain", "langchain"),
        ("langchain-core", "langchain_core"),
        ("langchain-community", "langchain_community"),
        ("pyttsx3", "pyttsx3"),
        ("SpeechRecognition", "speech_recognition"),
        ("sounddevice", "sounddevice"),
        ("scipy", "scipy"),
        ("openai-whisper", "whisper"),
        ("torch", "torch")
    ]

    if platform.system() == "Darwin":
        required += [
            ("Foundation", "Foundation"),
            ("pyobjc", "objc"),
            ("AppKit", "AppKit")
        ]

    for pip_name, module_name in required:
        if not is_installed(module_name):
            print(f"[SETUP] Installazione mancante: {pip_name}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", pip_name,
                    "--target", modules_dir
                ])
            except subprocess.CalledProcessError as e:
                print(f"[ERRORE] Installazione fallita per {pip_name}: {e}")
        else:
            print(f"[SETUP] ✓ {pip_name} già presente")

install_dependencies_if_needed()

# === 4. Flask server: Lazy init ===
_flask_server_started = False

def start_flask_server():
    global _flask_server_started
    if _flask_server_started:
        print("[DEBUG] Server Flask già avviato.")
        return

    try:
        from flask import Flask, request, jsonify
        import bpy
        from .utils import query_ollama_with_docs_async
    except ImportError as e:
        print("[ERRORE] Dipendenza mancante all’avvio del server:", e)
        return

    app = Flask(__name__)
    last_response = {"text": "", "ready": False}

    @app.route('/ask', methods=['POST'])
    def ask_question():
        data = request.json
        domanda = data.get('question', '')
        image_path = data.get('image_path', '')

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
                # selection_now = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
                # selected_objects = selection_now.copy()
                # query_ollama_with_docs_async(domanda, props, selected_objects, lambda: update_callback(props))
                selection_now = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
                selected_objects = selection_now.copy()

                # Selezione vuota e nessuna immagine → mostra messaggio e NON manda la query
                if not selected_objects and not image_path:
                    props.genai_response_text = "No object is currently selected in the scene. Please select one or more objects or upload an image."
                    last_response["text"] = props.genai_response_text
                    last_response["ready"] = True
                    return

                # ✅ Procedi: passiamo anche selected_objects vuoto, se c'è immagine
                query_ollama_with_docs_async(domanda, props, selected_objects, lambda: update_callback(props))


            except Exception as e:
                print("[ERRORE] Nel thread principale:", str(e))

        bpy.app.timers.register(run_in_main_thread)
        return jsonify({"status": "Domanda ricevuta da Blender"})

    @app.route('/response', methods=['GET'])
    def get_response():
        if last_response["ready"]:
            return jsonify({"status": "ready", "response": last_response["text"]})
        else:
            return jsonify({"status": "waiting"})

    print("[DEBUG] Server Flask avviato su http://127.0.0.1:5000")
    threading.Thread(target=lambda: app.run(host="127.0.0.1", port=5000), daemon=True).start()
    _flask_server_started = True