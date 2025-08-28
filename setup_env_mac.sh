#!/bin/bash
# === Setup pacchetti Python per Blender 4.5 su macOS ===

BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"
MODULES_DIR="$HOME/Library/Application Support/Blender/4.5/scripts/modules"

echo "[SETUP] Uso Python di Blender: $BLENDER_PY"
echo "[SETUP] Installerò i pacchetti in: $MODULES_DIR"

# Assicurati che pip sia disponibile
$BLENDER_PY -m ensurepip
$BLENDER_PY -m pip install --upgrade pip

# 🔧 Pulizia versioni NumPy sbagliate
echo "[SETUP] Pulisco vecchie versioni di numpy (2.x)..."
rm -rf "$MODULES_DIR"/numpy-2.*
rm -rf "$MODULES_DIR"/numpy-3.*

# 1. Installa NumPy 1.26.4 compatibile
echo "[SETUP] Installo numpy==1.26.4 (compatibile con Whisper + Numba)"
$BLENDER_PY -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 2. Installa openai-whisper senza dipendenze (così non forza numpy 2.x)
echo "[SETUP] Installo openai-whisper (senza dipendenze)"
$BLENDER_PY -m pip install --no-deps --upgrade openai-whisper --target "$MODULES_DIR"

# 3. Installa tutti gli altri pacchetti
echo "[SETUP] Installo pacchetti principali..."
$BLENDER_PY -m pip install \
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 \
    SpeechRecognition sounddevice scipy torch regex \
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers \
    pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz \
    --target "$MODULES_DIR" --upgrade

# 4. Reinstalla numpy 1.26.4 per sicurezza
echo "[SETUP] Reinstallo numpy==1.26.4 per sicurezza"
$BLENDER_PY -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 5. Installa PortAudio per sounddevice
if ! brew list portaudio &>/dev/null; then
    echo "[SETUP] Installo PortAudio con brew..."
    brew install portaudio
else
    echo "[SETUP] ✓ PortAudio già presente"
fi

# 6. Installa Ollama se manca
if ! command -v ollama &> /dev/null; then
    echo "[SETUP] Ollama non trovato. Lo installo..."
    curl -fsSL https://ollama.com/install.sh | sh
    hash -r  # aggiorna PATH in shell corrente
else
    echo "[SETUP] ✓ Ollama già presente"
fi

# 7. Pull modelli Ollama richiesti
echo "[SETUP] Scarico modelli Ollama richiesti..."
ollama pull llama3.2-vision
ollama pull llama3:instruct

# 8. Scarica modello Whisper (base, ~139MB) se manca
WHISPER_CACHE="$HOME/.cache/whisper"
mkdir -p "$WHISPER_CACHE"

if [ ! -f "$WHISPER_CACHE/base.pt" ]; then
    echo "[SETUP] Scarico modello Whisper (base, ~139MB) dal repo ufficiale OpenAI..."
    curl -L -o "$WHISPER_CACHE/base.pt" https://openaipublic.azureedge.net/main/whisper/models/base.pt
else
    echo "[SETUP] ✓ Modello Whisper (base) già presente"
fi


echo "[SETUP] ✅ Installazione completata!"
echo "[INFO] Per eseguire script con questi pacchetti usa sempre:"
echo "       $BLENDER_PY <script.py>"