import os
import sys
import platform
import threading
import traceback
import time
import queue

stop_recording_flag = threading.Event()
result_queue = queue.Queue()

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

print("[DEBUG] sys.path =")
for p in sys.path:
    print("   ", p)

try:
    from flask import Flask, jsonify
    import speech_recognition as sr
except ImportError as e:
    print(f"[ERRORE] Importazione moduli fallita: {e}")
    exit(1)

app = Flask(__name__)

# def background_listen(recognizer, mic, silence_timeout=5):
#     audio_chunks = []
#     last_talk = time.time()
#
#     with mic as source:
#         recognizer.adjust_for_ambient_noise(source)
#         print("[DEBUG] 🎙️ In ascolto...")
#
#         while not stop_recording_flag.is_set():
#             try:
#                 audio = recognizer.listen(source, timeout=5)
#                 audio_chunks.append(audio)
#                 last_talk = time.time()
#                 print("[DEBUG] 🗣️ Frase rilevata.")
#             except sr.WaitTimeoutError:
#                 tempo_trascorso = time.time() - last_talk
#                 print(f"[DEBUG] Silenzio da {tempo_trascorso:.2f}s...")
#                 if tempo_trascorso > silence_timeout:
#                     print("[DEBUG] 🤫 Silenzio prolungato → stop.")
#                     break
#
#     if audio_chunks:
#         combined = sr.AudioData(
#             b''.join(a.get_raw_data() for a in audio_chunks),
#             sample_rate=audio_chunks[0].sample_rate,
#             sample_width=audio_chunks[0].sample_width
#         )
#         try:
#             text = recognizer.recognize_google(combined, language="it-IT")
#             result_queue.put({"status": "ok", "text": text})
#         except sr.UnknownValueError:
#             result_queue.put({"status": "error", "error": "Voce non riconosciuta."})
#         except sr.RequestError as e:
#             result_queue.put({"status": "error", "error": str(e)})
#     else:
#         result_queue.put({"status": "error", "error": "Nessuna voce rilevata."})


# def background_listen(recognizer, mic, silence_timeout=15):
#     audio_chunks = []
#     last_talk = time.time()
#
#     recognizer.pause_threshold = 2.2  # aspetta 1.6s di silenzio prima di chiudere una frase
#     recognizer.non_speaking_duration = 0.4
#     recognizer.dynamic_energy_threshold = True
#
#     def callback(recognizer, audio):
#         nonlocal last_talk, audio_chunks
#         try:
#             # Test veloce per verificare se è parlato (anche silenzio ha waveform!)
#             if len(audio.get_raw_data()) > 400:
#                 print("[DEBUG] 🗣️ Segmento audio ricevuto.")
#                 audio_chunks.append(audio)
#                 last_talk = time.time()
#         except Exception as e:
#             print(f"[DEBUG] Errore nel callback: {e}")
#
#     stop_recording_flag.clear()
#     stop_listening = recognizer.listen_in_background(mic, callback)
#     print("[DEBUG] 🎙️ In ascolto continuo...")
#
#     grace_started = None
#
#     while not stop_recording_flag.is_set():
#         elapsed = time.time() - last_talk
#
#         if elapsed > silence_timeout:
#             if grace_started is None:
#                 grace_started = time.time()
#                 print("[DEBUG] ⚠️ Silenzio lungo, inizio grace period...")
#             elif time.time() - grace_started > 1.5:  # 🔁 1.5s extra
#                 print("[DEBUG] 🤫 Grace period finito → stop.")
#                 break
#         else:
#             grace_started = None
#
#         time.sleep(0.5)
#
#     stop_listening(wait_for_stop=False)
#
#     if audio_chunks:
#         combined = sr.AudioData(
#             b''.join(a.get_raw_data() for a in audio_chunks),
#             sample_rate=audio_chunks[0].sample_rate,
#             sample_width=audio_chunks[0].sample_width
#         )
#         try:
#             text = recognizer.recognize_google(combined, language="it-IT")
#             result_queue.put({"status": "ok", "text": text})
#         except sr.UnknownValueError:
#             result_queue.put({"status": "error", "error": "Voce non riconosciuta."})
#         except sr.RequestError as e:
#             result_queue.put({"status": "error", "error": str(e)})
#     else:
#         result_queue.put({"status": "error", "error": "Nessuna voce rilevata."})

def background_listen(recognizer=None, mic=None, max_duration=120):
    import audioop
    import numpy as np
    import tempfile
    from scipy.io import wavfile
    import whisper
    import time
    import os

    print("[DEBUG] 🎙️ Registrazione avviata.")
    stop_recording_flag.clear()
    result_queue.queue.clear()

    recognizer = sr.Recognizer()
    audio_chunks = []
    start_time = time.time()

    try:
        with sr.Microphone(sample_rate=16000) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            sample_rate = source.SAMPLE_RATE
            print(f"[DEBUG] 🔧 Microfono calibrato (SR={sample_rate})")

            while not stop_recording_flag.is_set():
                try:
                    frame = source.stream.read(1024)
                    rms = audioop.rms(frame, 2)
                    timestamp = time.time() - start_time
                    print(f"[DEBUG] 🕒 {timestamp:.2f}s | RMS={rms}")

                    if rms > 100:
                        audio_chunks.append(frame)
                except Exception as e:
                    print("[ERRORE] Lettura microfono fallita:", e)
                    break

                if time.time() - start_time > max_duration:
                    print("[DEBUG] ⏹️ Durata massima raggiunta.")
                    break

    except Exception as e:
        print("[ERRORE] Impossibile aprire microfono:", e)
        traceback.print_exc()
        result_queue.put({"status": "error", "error": str(e)})
        return

    if not audio_chunks:
        print("[DEBUG] ❌ Nessun audio registrato.")
        result_queue.put({"status": "error", "error": "Nessun audio utile."})
        return

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name
            audio_np = np.frombuffer(b''.join(audio_chunks), dtype=np.int16)
            wavfile.write(tmp_path, sample_rate, audio_np)
            print(f"[DEBUG] 💾 File WAV salvato temporaneamente: {tmp_path}")

        print("[DEBUG] 🤖 Trascrizione con Whisper in corso...")
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, language="en")
        text = result.get("text", "").strip()

        if text:
            print("[DEBUG] ✅ Testo trascritto:", text)
            result_queue.put({"status": "ok", "text": text})
        else:
            print("[DEBUG] ❌ Nessun testo riconosciuto.")
            result_queue.put({"status": "error", "error": "Voce non riconosciuta."})

    except Exception as e:
        print("[ERRORE] Whisper ha fallito:", str(e))
        result_queue.put({"status": "error", "error": str(e)})

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f"[DEBUG] 🧹 File temporaneo eliminato: {tmp_path}")



@app.route('/speech', methods=['GET'])
def speech_to_text():
    try:
        print("[DEBUG] ➤ Richiesta GET /speech ricevuta.")
        stop_recording_flag.clear()
        result_queue.queue.clear()

        recognizer = sr.Recognizer()
        mic = sr.Microphone(sample_rate=16000)

        thread = threading.Thread(target=background_listen, args=(recognizer, mic))
        thread.start()
        thread.join()

        if not result_queue.empty():
            return jsonify(result_queue.get())
        else:
            return jsonify({"status": "error", "error": "Nessun risultato."})
    except Exception as e:
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
