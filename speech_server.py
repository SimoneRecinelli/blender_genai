import os
import sys
import platform
import threading
import traceback

stop_recording_flag = threading.Event()

def get_modules_dir():
    blender_version = "4.4"  # cambia se aggiorni Blender
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

import sys
print("[DEBUG] sys.path =")
for p in sys.path:
    print("   ", p)

try:
    from flask import Flask, jsonify
    import sounddevice as sd
    import speech_recognition as sr
    import scipy.io.wavfile
    import tempfile
except ImportError as e:
    print(f"[ERRORE] Importazione moduli fallita: {e}")
    exit(1)

app = Flask(__name__)

@app.route('/speech', methods=['GET'])
def speech_to_text():
    try:
        print("[DEBUG] ➤ Richiesta GET /speech ricevuta.")

        samplerate = 16000
        duration = 5
        print("[DEBUG] 🎙️ Inizio registrazione audio...")

        recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            scipy.io.wavfile.write(f.name, samplerate, recording)
            audio_path = f.name

        print(f"[DEBUG] 💾 File WAV salvato in: {audio_path}")

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            print("[DEBUG] Inizio riconoscimento vocale...")

            try:
                text = recognizer.recognize_google(audio_data, language="it-IT")
                print(f"[DEBUG] 🗣️ Hai detto: {text}")
            except sr.UnknownValueError:
                print("[DEBUG] 🤷 Nessun parlato riconosciuto.")
                return jsonify({"status": "error", "error": "Voce non riconosciuta."})
            except sr.RequestError as e:
                print(f"[ERRORE] Errore richiesta a Google: {e}")
                return jsonify({"status": "error", "error": str(e)})

        os.remove(audio_path)
        print("[DEBUG] 🧹 File temporaneo rimosso.")
        return jsonify({"status": "ok", "text": text})

    except Exception as e:
        import traceback
        print("[ERRORE] Durante la dettatura:")
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)})


@app.route('/cancel', methods=['GET'])
def cancel_recording():
    print("[DEBUG] ❕ Richiesta /cancel ricevuta → interrompo registrazione.")
    stop_recording_flag.set()
    return jsonify({"status": "cancelled"})

if __name__ == '__main__':
    print("[DEBUG] ✅ Entrato nel main — avvio server Flask")
    print("[INFO] 🚀 Avvio server vocale su http://127.0.0.1:5056")
    app.run(port=5056)

