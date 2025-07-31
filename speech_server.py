import os
import sys
import platform
import threading
import traceback
import time
import queue

stop_recording_flag = threading.Event()
result_queue = queue.Queue()

# === Imposta sys.path per usare i moduli installati da server.py ===
def get_modules_dir():
    blender_version = "4.4"
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Application Support/Blender/{blender_version}/scripts/modules")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), f"Blender Foundation\\Blender\\{blender_version}\\scripts\\modules")
    elif platform.system() == "Linux":
        return os.path.expanduser(f"~/.config/blender/{blender_version}/scripts/modules")
    else:
        raise EnvironmentError("Sistema operativo non supportato")

modules_dir = get_modules_dir()
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# === Importa i moduli necessari (già installati) ===
from flask import Flask, jsonify
import whisper
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile

# === Inizializza Flask e Whisper ===
app = Flask(__name__)
whisper_model = whisper.load_model("base")

def background_listen(max_duration=120):
    print("[DEBUG] 🎙️ Registrazione avviata.")
    stop_recording_flag.clear()
    result_queue.queue.clear()

    sample_rate = 16000
    channels = 1
    dtype = 'int16'
    audio_buffer = []

    def callback(indata, frames, time_info, status):
        if stop_recording_flag.is_set():
            raise sd.CallbackStop()
        audio_buffer.append(indata.copy())

    try:
        with sd.InputStream(callback=callback, samplerate=sample_rate, channels=channels, dtype=dtype):
            start_time = time.time()
            while time.time() - start_time < max_duration:
                if stop_recording_flag.is_set():
                    print("[DEBUG] ❗️ Interruzione richiesta.")
                    break
                sd.sleep(200)
    except Exception as e:
        print("[ERRORE] Registrazione fallita:", str(e))
        traceback.print_exc()
        result_queue.put({"status": "error", "error": str(e)})
        return

    if not audio_buffer:
        print("[DEBUG] ❌ Nessun audio registrato.")
        result_queue.put({"status": "error", "error": "Nessun audio utile."})
        return

    try:
        audio_data = np.concatenate(audio_buffer, axis=0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name
            write(tmp_path, sample_rate, audio_data)
            print(f"[DEBUG] 💾 File WAV salvato: {tmp_path}")

        print("[DEBUG] 🤖 Avvio trascrizione...")
        result = whisper_model.transcribe(tmp_path, language="en")
        os.remove(tmp_path)

        text = result.get("text", "").strip()
        if text:
            print("[DEBUG] ✅ Testo trascritto:", text)
            result_queue.put({"status": "ok", "text": text})
        else:
            result_queue.put({"status": "error", "error": "Voce non riconosciuta."})

    except Exception as e:
        print("[ERRORE] Trascrizione fallita:", str(e))
        traceback.print_exc()
        result_queue.put({"status": "error", "error": str(e)})

@app.route('/speech', methods=['GET'])
def speech_to_text():
    print("[DEBUG] ➤ Richiesta GET /speech ricevuta.")
    stop_recording_flag.clear()
    result_queue.queue.clear()

    thread = threading.Thread(target=background_listen)
    thread.start()
    thread.join()

    if not result_queue.empty():
        return jsonify(result_queue.get())
    else:
        return jsonify({"status": "error", "error": "Nessun risultato."})

@app.route('/cancel', methods=['GET'])
def cancel_recording():
    print("[DEBUG] ❕ Richiesta /cancel ricevuta.")
    stop_recording_flag.set()
    return jsonify({"status": "cancelled"})

if __name__ == '__main__':
    print("[DEBUG] ✅ Server avviato su http://127.0.0.1:5056")
    app.run(port=5056)
