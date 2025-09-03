#!/bin/bash
# Setup ambiente Blender GenAI su macOS

BLENDER_PY="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"
MODULES_DIR="$HOME/Library/Application Support/Blender/4.5/scripts/modules"

echo "============================================"
echo "[SETUP] Blender GenAI Assistant - macOS"
echo "============================================"

# 0. Usa Python di Blender
echo "[SETUP] Uso Python di Blender: $BLENDER_PY"

"$BLENDER_PY" -m ensurepip
"$BLENDER_PY" -m pip install --upgrade pip

# 1. Pulizia versioni NumPy sbagliate
echo "[SETUP] Pulisco vecchie versioni di numpy (2.x/3.x)..."
rm -rf "$MODULES_DIR"/numpy-2.*
rm -rf "$MODULES_DIR"/numpy-3.*

# 2. Installa NumPy 1.26.4 compatibile (in modules_dir, isolato)
echo "[SETUP] Installo numpy==1.26.4"
"$BLENDER_PY" -m pip install --force-reinstall "numpy==1.26.4" --target "$MODULES_DIR"

# 3. Installa openai-whisper senza dipendenze in modules_dir
echo "[SETUP] Installo openai-whisper"
"$BLENDER_PY" -m pip install --upgrade openai-whisper --target "$MODULES_DIR"

# 4. Installa pacchetti principali nel Python di Blender, senza --target
echo "[SETUP] Installo pacchetti principali..."
"$BLENDER_PY" -m pip install --upgrade \
    faiss-cpu flask requests psutil PyMuPDF pyttsx3 \
    SpeechRecognition sounddevice scipy torch regex \
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers \
    PyQt5 pyobjc

# 5. Installa PortAudio per sounddevice
if ! brew list portaudio &>/dev/null; then
    echo "[SETUP] Installo PortAudio con Homebrew..."
    brew install portaudio
else
    echo "[SETUP] ✓ PortAudio già presente"
fi

# 6. Installa Ollama se manca
if ! command -v ollama &> /dev/null; then
    echo "[SETUP] Ollama non trovato. Lo installo..."
    curl -fsSL https://ollama.com/install.sh | sh
    hash -r
else
    echo "[SETUP] ✓ Ollama già presente"
fi

# 7. Avvia Ollama come servizio
echo "[SETUP] Avvio Ollama..."
(ollama serve > /dev/null 2>&1 &)
sleep 5

# 8. Pull modelli Ollama richiesti
echo "[SETUP] Scarico modelli Ollama richiesti..."
ollama pull llama3.2-vision
ollama pull llama3:instruct

# 9. Scarica modello Whisper se manca
WHISPER_CACHE="$HOME/.cache/whisper"
mkdir -p "$WHISPER_CACHE"
if [ ! -f "$WHISPER_CACHE/base.pt" ]; then
    echo "[SETUP] Scarico modello Whisper (base)..."
    curl -L -o "$WHISPER_CACHE/base.pt" https://openaipublic.azureedge.net/main/whisper/models/base.pt
else
    echo "[SETUP] ✓ Modello Whisper (base) già presente"
fi

echo "============================================"
echo "[SETUP] ✅ Installazione completata!"
echo "============================================"
