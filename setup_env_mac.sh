#!/bin/bash
# === Setup pacchetti Python per Blender 4.5 su macOS ===

BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"
MODULES_DIR="$HOME/Library/Application Support/Blender/4.5/scripts/modules"

echo "[SETUP] Uso Python di Blender: $BLENDER_PY"
echo "[SETUP] Installerò i pacchetti in: $MODULES_DIR"

# assicurati che pip sia disponibile
$BLENDER_PY -m ensurepip
$BLENDER_PY -m pip install --upgrade pip

# 1. Blocca numpy alla versione compatibile
$BLENDER_PY -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 2. Installa openai-whisper senza dipendenze (così non forza numpy 2.x)
$BLENDER_PY -m pip install --no-deps --upgrade openai-whisper --target "$MODULES_DIR"

# 3. Installa tutti gli altri pacchetti
$BLENDER_PY -m pip install \
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 \
    SpeechRecognition sounddevice scipy torch regex \
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers \
    pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz \
    --target "$MODULES_DIR"

# === Installazione Ollama se manca ===
if ! command -v ollama &> /dev/null; then
    echo "[SETUP] Ollama non trovato. Lo installo..."
    curl -fsSL https://ollama.com/install.sh | sh
    hash -r  # aggiorna PATH in shell corrente
else
    echo "[SETUP] ✓ Ollama già presente"
fi

# === Pull modelli ===
echo "[SETUP] Scarico modelli Ollama richiesti..."
ollama pull llama3.2-vision
ollama pull llama3:instruct

echo "[SETUP] ✅ Installazione completata!"
