<div align="center">
  <img src="icons/logo.png" alt="Blender GenAI Logo" width="240"/>

  <p>
    <img src="https://forthebadge.com/images/badges/built-with-love.svg"/>
    <img src="https://forthebadge.com/images/badges/works-on-my-machine.svg"/>
    <br>
    <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white&style=for-the-badge"/>
    <img src="https://img.shields.io/badge/Blender-4.4-orange?logo=blender&logoColor=white&style=for-the-badge"/>
    <img src="https://img.shields.io/badge/PyQt5-GUI-brightgreen?logo=qt&logoColor=white&style=for-the-badge"/>
    <img src="https://img.shields.io/badge/Flask-Server-black?logo=flask&logoColor=white&style=for-the-badge"/>
  </p>


  <h1> 🤖 Blender GenAI Assistant 🤖</h1>
  <p>
    Assistente AI per la modellazione 3D in Blender, potenziato da modelli linguistici e multimodali.
  </p>
</div>


Questo progetto propone un sistema di supporto intelligente per Blender, basato su modelli GenAI per assistere nella modellazione 3D in modo contestuale e multimodale.
Sviluppato per il corso di **Computer Graphics & Multimedia** (A.A. 2024/2025) presso l’**Università Politecnica delle Marche**, tenuto dal **Prof. Primo Zingaretti**, coadiuvato dai tutor **Emanuele Balloni** e **Lorenzo Stacchio**.
Realizzato da **Simone Recinelli**, **Diego Santarelli** e **Andrea Marini**.
---

## 🇮🇹 Versione italiana (Italian version)

Questo repository contiene un addon per Blender che integra un assistente AI basato su LLM, capace di rispondere a domande tecniche e contestuali grazie a un sistema RAG (Retrieval-Augmented Generation).

---

## 📌 Funzionalità principali

- 🔍 **Assistenza contestuale** sulle operazioni di modellazione
- 📷 **Comprensione visuale** della scena con input immagine
- 🧠 **Suggerimenti intelligenti** in base alla scena e selezione corrente
- 📚 **Sistema RAG** con ricerca semantica nella documentazione Blender
- 💬 **Interfaccia esterna PyQt5** con cronologia e tema dark/light
- ⚙️ **Compatibilità multi-piattaforma**: macOS Apple Silicon & Windows
- 🎛️ **Prompt dinamico** in base a testo o immagine inviata

---

## 🧹 Struttura del progetto

```
blender_genai/
├── __init__.py                # Entry point per l'addon
├── panel.py                   # UI in Blender (chat, immagine, toggle)
├── genai_operator.py          # Operatore per interazione con AI
├── utils.py                   # Funzioni core, modelli, RAG
├── server.py                  # Server Flask + auto install dipendenze
├── extern_gui.py              # Interfaccia esterna PyQt5
├── langchain_rag_blender.py   # Logica RAG e indexing
├── icons/                     # Icone SVG/Pixmap
└── README.md                  # Questo file
```

---

## 🛠️ Tecnologie utilizzate

| Stack       | Tecnologie |
|-------------|------------|
| AI Backend  | Ollama + LLaMA3, LLaVA, SentenceTransformers |
| Retrieval   | FAISS, LangChain, HuggingFace embeddings |
| Frontend    | Blender UI API, PyQt5 esterno |
| Server      | Flask REST API |
| Piattaforme | Blender 4.4+, Python 3.11, macOS & Windows |

---

## ⚖️ Documentazione Blender (PDF)

Per permettere l'elaborazione della documentazione ufficiale di Blender **in locale**, il repository include il file `Blender_doc.pdf`.

> ⚠️ **Nota**: il file è gestito tramite **Git LFS**, poiché supera i 100MB.

### Installare Git LFS (solo una volta):

```bash
# macOS (Homebrew)
brew install git-lfs

# Ubuntu/Debian
sudo apt install git-lfs

git lfs install
```

---

## ⚙️ Requisiti & Setup

### ✅ Dipendenze Python: installazione automatica

Non è necessario installare manualmente pacchetti Python:  
le dipendenze vengono installate **automaticamente all’avvio dell’addon** tramite `server.py` in:

```
~/Library/Application Support/Blender/4.4/scripts/modules/
```

Dipendenze incluse:
- Flask
- FAISS
- sentence-transformers
- langchain-core + langchain-community
- PyMuPDF
- PyQt5
- psutil
- requests
- pyobjc (solo macOS)

### 📦 Clonare il repository

```bash
git lfs install
git clone https://github.com/SimoneRecinelli/blender_genai.git
```

Se hai già clonato il repo **senza Git LFS**, puoi sistemare così:
```bash
git lfs install
git lfs pull
```

---


## 📊 Demo

https://user-images.githubusercontent.com/123456789/xyz/demo_video.mp4  
*(Inserire video reale o GIF dimostrativa)*

---


## 🔍 Esempi d'uso

- "Come si fa un bevel su un oggetto selezionato?"
- "Analizza questo modello: è troppo poligonale?"
- "Che materiali posso usare in Cycles per il vetro?"

---

## 👨‍💼 Autori

- Simone Recinelli  
- Diego Santarelli  
- Andrea Marini  

Progetto universitario per il corso **Computer Graphics & Multimedia** (A.A. 2024/25)  
Università Politecnica delle Marche  
Prof. Primo Zingaretti  
Tutor: Emanuele Balloni, Lorenzo Stacchio

---

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.

---

## 🇬🇧 English version

> ✨ This repository contains a Blender addon that integrates an AI assistant based on large language and vision models (LLM/MLLM). It can provide technical and contextual support to users during the 3D modeling process, thanks to a RAG (Retrieval-Augmented Generation) system over the official Blender documentation.

**Main Features:**
- Ask Blender-related questions in natural language
- Send a screenshot of the viewport to get visual feedback
- Get modeling tips, Python automation help, and usage explanations
- RAG system for contextual responses from the Blender manual
- External GUI (PyQt5) with light/dark theme and history
- Automatic Python dependency installer via `server.py`

Built with ❤️ by Simone Recinelli, Diego Santarelli, and Andrea Marini.
