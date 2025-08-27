#!/bin/bash
# === Setup pacchetti Python per Blender 4.5 su macOS ===

BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"
MODULES_DIR="$HOME/Library/Application Support/Blender/4.5/scripts/modules"

echo "[SETUP] Uso Python di Blender: $BLENDER_PY"
echo "[SETUP] Installerò i pacchetti in: $MODULES_DIR"

# assicurati che pip sia disponibile
$BLENDER_PY -m ensurepip
$BLENDER_PY -m pip install --upgrade pip

# installa i pacchetti richiesti
$BLENDER_PY -m pip install \
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 \
    SpeechRecognition sounddevice scipy openai-whisper torch "numpy==1.26.4" regex \
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers \
    pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz \
    --target "$MODULES_DIR"

echo "[SETUP] ✅ Installazione completata!"
