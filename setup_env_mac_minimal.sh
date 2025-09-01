#!/bin/bash
# === Setup ambiente Blender GenAI su macOS (MINIMAL) ===

BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"
MODULES_DIR="$HOME/Library/Application Support/Blender/4.5/scripts/modules"

echo "============================================"
echo "[SETUP] Blender GenAI Assistant - macOS (MINIMAL)"
echo "============================================"

# 0. Usa Python di Blender
echo "[SETUP] Uso Python di Blender: $BLENDER_PY"
echo "[SETUP] Installerò i pacchetti in: $MODULES_DIR"

"$BLENDER_PY" -m ensurepip
"$BLENDER_PY" -m pip install --upgrade pip

# 1. Pulizia versioni NumPy sbagliate
echo "[SETUP] Pulisco vecchie versioni di numpy (2.x/3.x)..."
rm -rf "$MODULES_DIR"/numpy-2.*
rm -rf "$MODULES_DIR"/numpy-3.*

# 2. Installa NumPy 1.26.4 compatibile
echo "[SETUP] Installo numpy==1.26.4"
"$BLENDER_PY" -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 3. Installa openai-whisper senza dipendenze
echo "[SETUP] Installo openai-whisper (senza dipendenze)"
"$BLENDER_PY" -m pip install --no-deps --upgrade openai-whisper --target "$MODULES_DIR"

# 4. Installa pacchetti principali
echo "[SETUP] Installo pacchetti principali..."
"$BLENDER_PY" -m pip install \
    faiss-cpu flask requests psutil PyMuPDF pyttsx3 \
    SpeechRecognition sounddevice scipy torch regex \
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers \
    pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz \
    --target "$MODULES_DIR" --upgrade

# 5. Installa PyQt5 con Homebrew (più stabile su macOS ARM)
if ! brew list pyqt@5 &>/dev/null; then
    echo "[SETUP] Installo PyQt5 con Homebrew..."
    brew install pyqt@5
else
    echo "[SETUP] ✓ PyQt5 già presente"
fi

# 6. Reinstalla numpy per sicurezza
"$BLENDER_PY" -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 7. Installa PortAudio (per sounddevice)
if ! brew list portaudio &>/dev/null; then
    echo "[SETUP] Installo PortAudio con Homebrew..."
    brew install portaudio
else
    echo "[SETUP] ✓ PortAudio già presente"
fi

# 8. Installa Ollama se manca
if ! command -v ollama &> /dev/null; then
    echo "[SETUP] Ollama non trovato. Lo installo..."
    curl -fsSL https://ollama.com/install.sh | sh
    hash -r
else
    echo "[SETUP] ✓ Ollama già presente"
fi

# 9. Avvia Ollama come servizio
echo "[SETUP] Avvio Ollama..."
(ollama serve > /dev/null 2>&1 &)
sleep 5

# 10. Pull modelli Ollama richiesti
echo "[SETUP] Scarico modelli Ollama richiesti..."
ollama pull llama3.2-vision
ollama pull llama3:instruct

# 11. Scarica modello Whisper base (~139MB) se manca
WHISPER_CACHE="$HOME/.cache/whisper"
mkdir -p "$WHISPER_CACHE"
if [ ! -f "$WHISPER_CACHE/base.pt" ]; then
    echo "[SETUP] Scarico modello Whisper (base)..."
    curl -L -o "$WHISPER_CACHE/base.pt" https://openaipublic.azureedge.net/main/whisper/models/base.pt
else
    echo "[SETUP] ✓ Modello Whisper (base) già presente"
fi

echo "============================================"
echo "[SETUP] ✅ Installazione completata (MINIMAL)!"
echo "============================================"
