@echo off
REM === Setup pacchetti Python per Blender 4.5 su Windows ===

set "BLENDER_PY=C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe"
set "MODULES_DIR=%APPDATA%\Blender Foundation\Blender\4.5\scripts\modules"

echo [SETUP] Uso Python di Blender: %BLENDER_PY%
echo [SETUP] Installerò i pacchetti in: %MODULES_DIR%

"%BLENDER_PY%" -m ensurepip
"%BLENDER_PY%" -m pip install --upgrade pip

REM 1. Blocca numpy alla versione compatibile
"%BLENDER_PY%" -m pip install --force-reinstall "numpy==1.26.4" --target "%MODULES_DIR%"

REM 2. Installa openai-whisper senza dipendenze
"%BLENDER_PY%" -m pip install --no-deps --upgrade openai-whisper --target "%MODULES_DIR%"

REM 3. Installa tutti gli altri pacchetti
"%BLENDER_PY%" -m pip install ^
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 ^
    SpeechRecognition sounddevice scipy torch regex ^
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers ^
    --target "%MODULES_DIR%"

echo [SETUP] Controllo Ollama...

where ollama >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [SETUP] Ollama non trovato. Lo installo...
    powershell -Command "Invoke-WebRequest https://ollama.com/download/OllamaSetup.exe -OutFile ollama_installer.exe"
    start /wait ollama_installer.exe
    del ollama_installer.exe
) else (
    echo [SETUP] ✓ Ollama già presente
)

echo [SETUP] Scarico modelli Ollama richiesti...
ollama pull llama3.2-vision
ollama pull llama3:instruct

echo [SETUP] ✅ Installazione completata!
pause
