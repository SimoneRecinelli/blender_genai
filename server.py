import sys, os, platform, threading, time, shutil, ctypes

# === 1. Aggiungi la cartella 'scripts/modules' di Blender a sys.path ===
try:
    import bpy
    modules_dir = bpy.utils.user_resource('SCRIPTS', path="modules", create=True)
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
except Exception as e:
    print(f"[ERRORE] Impossibile accedere a bpy o user_resource: {e}")
    modules_dir = None


# === 2. Determina la cartella modules in base al sistema operativo ===
def get_modules_dir():
    try:
        import bpy
        major, minor, _ = bpy.app.version  # es. (4, 5, 0)
        blender_version = f"{major}.{minor}"
    except Exception:
        blender_version = "4.5"  # fallback se lanci fuori da Blender

    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Application Support/Blender/{blender_version}/scripts/modules")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), f"Blender Foundation\\Blender\\{blender_version}\\scripts\\modules")
    else:
        return os.path.expanduser(f"~/.config/blender/{blender_version}/scripts/modules")


modules_dir = get_modules_dir()
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


# ========= Helper Windows per elevazione UAC =========
def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def _run_elevated_powershell(ps_command: str, show_window=True):
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", "powershell.exe",
        f'-NoProfile -ExecutionPolicy Bypass -Command "{ps_command}"',
        None, 1 if show_window else 0
    )


def _wait_until_ffmpeg_ready(timeout_sec=240, interval_sec=3):
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        if shutil.which("ffmpeg") is not None:
            return True
        candidate = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
        if os.path.isfile(candidate):
            os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH", "")
            if shutil.which("ffmpeg"):
                return True
        time.sleep(interval_sec)
    return False


# === 3. Installazione ffmpeg se manca ===
def install_ffmpeg_if_needed():
    if shutil.which("ffmpeg") is not None:
        print("[SETUP] ✓ ffmpeg già presente")
        return

    print("[SETUP] ❌ ffmpeg non trovato. Provo a installarlo...")

    system = platform.system()

    if system == "Darwin":
        # macOS – usa Homebrew
        if shutil.which("brew") is None:
            print("[ERRORE] Homebrew non installato. Installa prima brew da https://brew.sh/")
            return
        try:
            subprocess.check_call(["brew", "install", "ffmpeg"])
            print("[SETUP] ✅ ffmpeg installato con brew")
        except subprocess.CalledProcessError as e:
            print(f"[ERRORE] Installazione ffmpeg fallita: {e}")

    elif system == "Linux":
        try:
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "ffmpeg"])
            print("[SETUP] ✅ ffmpeg installato con apt")
        except subprocess.CalledProcessError as e:
            print(f"[ERRORE] Installazione ffmpeg fallita: {e}")

    elif system == "Windows":
        def _install_with_choco_here():
            try:
                subprocess.check_call(["choco", "install", "-y", "ffmpeg"])
                print("[SETUP] ✅ ffmpeg installato con Chocolatey.")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"[ATTENZIONE] choco non disponibile o installazione fallita qui: {e}")
                return False

        if _is_admin() and shutil.which("choco"):
            if _install_with_choco_here():
                return

        ps_script = r"""
        $ErrorActionPreference = 'Stop'
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
          Write-Host '>> Installing Chocolatey...'
          Set-ExecutionPolicy Bypass -Scope Process -Force
          [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
          iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        }
        try { choco upgrade chocolatey -y } catch { Write-Warning $_ }
        Write-Host '>> Installing ffmpeg via choco...'
        choco install -y ffmpeg
        exit 0
        """

        print("[SETUP] ↪ Richiesta elevazione (UAC) per installare Chocolatey e ffmpeg...")
        _run_elevated_powershell(ps_script)

        if _wait_until_ffmpeg_ready(timeout_sec=240):
            print("[SETUP] ✅ ffmpeg installato e disponibile.")
        else:
            print("[SETUP] Non riesco a verificare automaticamente ffmpeg.")
            print("Se hai rifiutato il prompt UAC, riavvia Blender come Amministratore oppure installa manualmente:")
            print("1) Apri PowerShell come Admin")
            print("2) choco install -y ffmpeg")

    else:
        print("[ERRORE] Sistema operativo non supportato per l’installazione automatica di ffmpeg.")


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
        print("⚠️ Esegui prima setup_env_mac.sh o setup_env_win.bat")
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

        def run_in_main_thread():
            try:
                props = bpy.context.scene.genai_props
                props.genai_question = domanda
                props.genai_image_path = image_path

                selection_now = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
                selected_objects = selection_now.copy()

                def update_callback(props):
                    print("[Flask] ✅ Risposta generata da Ollama!")
                    last_response["text"] = props.genai_response_text
                    last_response["ready"] = True

                try:
                    query_ollama_with_docs_async(domanda, props, selected_objects, lambda: update_callback(props))
                except Exception as e:
                    print("[ERRORE] Query async fallita:", str(e))
                    props.genai_response_text = f"[Errore interno] {str(e)}"
                    last_response["text"] = props.genai_response_text
                    last_response["ready"] = True

            except Exception as e:
                print("[ERRORE] Nel thread principale:", str(e))
                if "props" in locals():
                    props.genai_response_text = f"[Errore interno] {str(e)}"
                    last_response["text"] = props.genai_response_text
                else:
                    last_response["text"] = f"[Errore interno] {str(e)}"
                last_response["ready"] = True

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
