@echo off
REM === Setup pacchetti Python per Blender 4.5 su Windows ===

set BLENDER_PY="C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe"
set MODULES_DIR=%APPDATA%\Blender Foundation\Blender\4.5\scripts\modules

echo [SETUP] Uso Python di Blender: %BLENDER_PY%
echo [SETUP] Installerò i pacchetti in: %MODULES_DIR%

%BLENDER_PY% -m ensurepip
%BLENDER_PY% -m pip install --upgrade pip

%BLENDER_PY% -m pip install ^
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 ^
    SpeechRecognition sounddevice scipy openai-whisper torch numpy==1.26.4 regex ^
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers ^
    --target "%MODULES_DIR%"

echo [SETUP] ✅ Installazione completata!
pause
