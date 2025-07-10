from flask import Flask, request, jsonify
import threading
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

    # Reset risposta
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
            print("[ERRORE] Durante l'esecuzione nel thread principale:", str(e))
        return None

    # 🔁 Esegui nel thread principale di Blender
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

_flask_server_started = False  # Variabile globale per evitare doppio avvio

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
