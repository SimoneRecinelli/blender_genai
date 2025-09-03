@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM === Setup ambiente Blender GenAI su Windows (FULL) ===
SET "BLENDER_PY=C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe"
SET "MODULES_DIR=%APPDATA%\Blender Foundation\Blender\4.5\scripts\modules"

echo ============================================
echo [SETUP] Blender GenAI Assistant - Windows (FULL)
echo ============================================

REM 0. Installa Chocolatey se manca (per Git e Python)
where choco >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Chocolatey non trovato. Lo installo...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
       [System.Net.ServicePointManager]::SecurityProtocol = 'Tls12'; ^
       iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
) else (
    echo [SETUP] ✓ Chocolatey gia' presente
)

REM 1. Installa Git se manca
where git >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Git non trovato. Lo installo con choco...
    choco install -y git
) else (
    echo [SETUP] ✓ Git gia' presente
)

REM 2. Installa Python (di sistema) se manca
where python >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Python non trovato. Lo installo con choco...
    choco install -y python
) else (
    echo [SETUP] ✓ Python gia' presente
)

REM 3. Usa Python di Blender
echo [SETUP] Uso Python di Blender: %BLENDER_PY%
echo [SETUP] Installerò i pacchetti in: %MODULES_DIR%

"%BLENDER_PY%" -m ensurepip
"%BLENDER_PY%" -m pip install --upgrade pip

REM 4. Pulizia numpy sbagliati
echo [SETUP] Pulizia versioni numpy 2.x/3.x...
del /Q "%MODULES_DIR%\numpy-2.*" >nul 2>nul
del /Q "%MODULES_DIR%\numpy-3.*" >nul 2>nul

REM 5. Installa numpy compatibile
"%BLENDER_PY%" -m pip install --force-reinstall "numpy==1.26.4" --target "%MODULES_DIR%"

REM 6. Installa openai-whisper senza dipendenze
"%BLENDER_PY%" -m pip install --no-deps --upgrade openai-whisper --target "%MODULES_DIR%"

REM 7. Installa pacchetti principali
"%BLENDER_PY%" -m pip install ^
    faiss-cpu flask requests PyQt5 psutil PyMuPDF pyttsx3 ^
    SpeechRecognition sounddevice scipy torch regex ^
    langchain langchain-core langchain-community langchain-huggingface sentence-transformers ^
    --target "%MODULES_DIR%" --upgrade

REM
"%BLENDER_PY%" -m pip install --force-reinstall "numpy==1.26.4" --target "%MODULES_DIR%"

REM 9. Installa pyaudio (usa PortAudio incluso)
"%BLENDER_PY%" -m pip install pyaudio --target "%MODULES_DIR%" --upgrade

REM 10. Installa Ollama se manca
where ollama >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Ollama non trovato. Lo installo...
    powershell -Command "Invoke-WebRequest https://ollama.com/download/OllamaSetup.exe -OutFile ollama_installer.exe; Start-Process ollama_installer.exe -Wait"
) else (
    echo [SETUP] ✓ Ollama gia' presente
)

REM 11. Avvia Ollama in background
echo [SETUP] Avvio Ollama...
start /B ollama serve
timeout /t 5 >nul

REM 12. Pull modelli Ollama
ollama pull llama3.2-vision
ollama pull llama3:instruct

REM 13. Scarica modello Whisper base
set "WHISPER_CACHE=%USERPROFILE%\.cache\whisper"
if not exist "%WHISPER_CACHE%" mkdir "%WHISPER_CACHE%"

if not exist "%WHISPER_CACHE%\base.pt" (
    echo [SETUP] Scarico modello Whisper (base, ~139MB)...
    powershell -Command "Invoke-WebRequest https://openaipublic.azureedge.net/main/whisper/models/base.pt -OutFile '%WHISPER_CACHE%\base.pt'"
) else (
    echo [SETUP] ✓ Modello Whisper base gia' presente
)

echo ============================================
echo [SETUP] ✅ Installazione completata!
echo ============================================
pause
