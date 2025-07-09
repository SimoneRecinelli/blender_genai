import sys
import os

from flask import Flask, request, jsonify
import threading
import subprocess
import bpy
from .utils import query_ollama_with_docs_async

app = Flask(__name__)

# Variabile globale per la risposta generata
last_response = {"text": "", "ready": False}

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    domanda = data.get('question', '')
    image_path = data.get('image_path', '')

    props = bpy.context.scene.genai_props
    props.genai_question = domanda
    props.genai_image_path = image_path

    # Reset risposta
    last_response["text"] = ""
    last_response["ready"] = False

    def update_callback():
        print("[Flask] ✅ Risposta generata da Ollama!")
        last_response["text"] = props.genai_response_text
        last_response["ready"] = True

    def run_in_main_thread():
        try:
            selected_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
            query_ollama_with_docs_async(domanda, props, selected_objects, update_callback)
        except Exception as e:
            print("[ERRORE] Durante il recupero degli oggetti selezionati:", str(e))
        return None

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
        print("[DEBUG] Server Flask avviato su http://localhost:5000")
        threading.Thread(
            target=lambda: app.run(host="127.0.0.1", port=5000),
            daemon=True
        ).start()
        _flask_server_started = True
    else:
        print("[DEBUG] Server Flask già attivo, non viene riavviato.")

def start_gui():
    if try_bring_gui_to_front():
        print("[DEBUG] GUI già attiva → portata in primo piano.")
        return

    gui_path = os.path.join(os.path.dirname(__file__), "extern_gui.py")
    try:
        subprocess.Popen([sys.executable, gui_path])
        print("[DEBUG] GUI PyQt5 avviata")
    except Exception as e:
        print("[ERRORE] Avvio GUI PyQt5:", e)

def try_bring_gui_to_front():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 5055))
        s.send(b"bring-to-front")
        s.close()
        return True
    except Exception as e:
        print("[DEBUG] Nessuna GUI attiva → motivo:", e)
        return False
