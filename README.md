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
    Questo progetto propone un sistema di supporto intelligente per Blender, basato su modelli GenAI per assistere nella modellazione 3D in modo contestuale e multimodale.

Sviluppato per il corso di **Computer Graphics & Multimedia** (A.A. 2024/2025) presso l’**Università Politecnica delle Marche**, tenuto dal **Prof. Primo Zingaretti**, coadiuvato dai tutor **Emanuele Balloni** e **Lorenzo Stacchio**.

Realizzato da **Simone Recinelli**, **Diego Santarelli** e **Andrea Marini**.
  </p>
</div>

---


## 👆🏼 Indice

- [📌 Funzionalità del sistema](#-funzionalità-del-sistema)
- [🧹 Struttura del progetto](#-struttura-del-progetto)
- [🛠️ Tecnologie utilizzate](#️-tecnologie-utilizzate)
- [⚖️ Documentazione Blender (PDF)](#️-documentazione-blender-pdf)
- [⚙️ Requisiti & Setup](#️-requisiti--setup)
  - [✅ Dipendenze Python: installazione automatica](#-dipendenze-python-installazione-automatica)
  - [📦 Clonare il repository](#-clonare-il-repository)
  - [📥 Installare laddon su Blender](#-installare-laddon-su-blender)
  - [🚀 Avviare l'interfaccia](#-avviare-linterfaccia)
- [🪟 Interfaccia Esterna del Chatbot](#-interfaccia-esterna-del-chatbot)
  - [✨ Caratteristiche principali della GUI](#-caratteristiche-principali-della-gui)
- [📊 Demo](#-demo)
- [👨‍💼 Autori](#-autori)
- [📄 Licenza](#-licenza)


---

## 📌 Funzionalità del sistema

Il sistema Blender GenAI Assistant integra strumenti intelligenti per assistere l’utente nella modellazione 3D in modo contestuale, multimodale e interattivo. Le funzionalità sono accessibili sia da Blender che da un’interfaccia grafica esterna.

- 🧠 **Assistenza intelligente** alla modellazione
  - 🔍 **Suggerimenti contestuali** su operazioni, strumenti e tecniche avanzate
  - 📚 **Sistema RAG** integrato con ricerca semantica nella documentazione Blender
  - 🧠 **Prompt dinamico** che include automaticamente dettagli della scena, selezione attiva e stato del modello
  - 🧪 **Analisi tecnica** del modello selezionato: vertici, UV, manifold, normali invertite, materiali, modificatori, ecc.
- 💬 Interfaccia grafica (GUI) esterna
  - 🪟 **GUI PyQt5 esterna** separata da Blender, in stile chat moderna
  - 💡 **Tema scuro/chiaro dinamico** in base alle preferenze Blender
  - 🔁 **Gestione asincrona** delle risposte AI, senza blocchi dell’interfaccia
  - 💾 **Storico chat persistente**, con salvataggio automatico
- 🖼️ **Multimodalità e visualizzazione**
  - 📷 **Cattura automatica di screenshot** da Blender con anteprima in GUI
  - 🧠 **Input visuale nel prompt**, utile per scene complesse o debugging visivo
- 🎙️ **Interazione vocale**
  - 🎤 **Dettatura vocale** delle domande via server Flask con Whisper (fino a 2 min, con silenzio automatico)
  - 🔊 **Lettura vocale** delle risposte generate (TTS, es. voce "Samantha" su macOS)
- ⚙️ **Automazioni e compatibilità**
  - 🔄 **Installazione automatica delle dipendenze** Python in scripts/modules/ di Blender
  - 🔒 **Avvio singleton della GUI**, riportata in primo piano se già aperta
  - 🧹 **Reset automatico della chat** alla chiusura di Blender o dell’interfaccia
  - 🧠 **Script dedicato per indicizzazione documentazione PDF**, integrato con LangChain e FAISS

---

## 🧹 Struttura del progetto

```
blender_genai/
├── icons/                     # Icone SVG/Pixmap
├── __init__.py                # Entry point per l'addon
├── panel.py                   # UI in Blender (chat, immagine, toggle)
├── genai_operator.py          # Operatore per interazione con AI
├── utils.py                   # Funzioni core, modelli, RAG
├── server.py                  # Server Flask + auto install dipendenze
├── extern_gui.py              # Interfaccia esterna PyQt5
├── langchain_rag_blender.py   # Logica RAG e indexing
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
- [Flask](https://flask.palletsprojects.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [sentence-transformers](https://www.sbert.net/)
- [langchain-core](https://docs.langchain.com/docs/components/langchain-core) + [langchain-community](https://github.com/langchain-ai/langchain)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [PyQt5](https://riverbankcomputing.com/software/pyqt/)
- [psutil](https://psutil.readthedocs.io/)
- [requests](https://requests.readthedocs.io/)
- [pyobjc](https://pyobjc.readthedocs.io/en/latest/) *(macOS only)*


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

### 📥 Installare l'addon su Blender
Per installare il progetto come addon Blender:

1. Comprimi la cartella blender_genai in un file ".zip".
2. Apri Blender.
3. Vai su Modifica > Preferenze > Add-ons.
4. Clicca sull’icona a freccia in alto a destra e scegli “Install from Disk”.
5. Seleziona lo .zip appena creato e conferma.
6. Spunta la casella per attivare l’addon.

### 🚀 Avviare l’interfaccia
Una volta installato l’addon:

1. Premi N per aprire la sidebar a destra nella 3D View.
2. Vai nella sezione GenAI.
3. Clicca sul bottone “Apri Chat Esterna” per lanciare l’interfaccia PyQt5.

Da qui potrai:

- 💬 Chattare con l’assistente in tempo reale
- 🖼️ Inviare screenshot della scena Blender
- 🤖 Ottenere risposte intelligenti, documentate e multimodali

---

## 🪟 Interfaccia del Chatbot

L’addon include una interfaccia grafica personalizzata esterna sviluppata in PyQt5, progettata per offrire un'esperienza utente fluida e moderna, ispirata alle applicazioni di messaggistica.È completamente multi-piattaforma (macOS Apple Silicon e Windows), supporta la cronologia delle conversazioni, invio di immagini della scena Blender, e la modalità dark/light con switch dinamico.

#### ✨ Caratteristiche principali della GUI:

- ✅ Interfaccia separata da Blender, con comunicazione socket asincrona

- 💬 Area di chat con storico persistente e salvataggio automatico

- 🖼️ Supporto per l’invio di screenshot dalla scena Blender

- 🌗 Tema chiaro/scuro attivabile con uno switch animato

- ⌨️ Invio con Enter e a capo con Shift+Enter

- 🔁 Integrazione con il sistema RAG per risposte documentate

- 🎙️ Pulsante microfono per **dettatura vocale** delle domande

- 🔊 Pulsante audio per **lettura vocale** delle risposte del chatbot

- 📁 Il file dell’interfaccia è extern_gui.py, e si avvia automaticamente cliccando il bottone 'Apri Chat' all’interno del pannello Blender.

Una volta catturata la schermata in Blender, l'immagine compare in anteprima nella GUI: può essere cliccata per visualizzarla a schermo intero ed è accompagnata da un'icona del cestino per eliminarla e caricarne una nuova, se desiderato.

Di seguito si allegano due screen dell'interfaccia del chatbot realizzato, rispettivamente in light mode e dark mode:

<p align="center">
  <img src="icons/light_mode.png" alt="Interfaccia PyQt5 del chatbot GenAI Assistant" width="600"/>
</p>

<p align="center">
  <img src="icons/dark_mode.png" alt="Interfaccia PyQt5 del chatbot GenAI Assistant" width="600"/>
</p>


---

## 📊 Demo

https://user-images.githubusercontent.com/123456789/xyz/demo_video.mp4  
*(Inserire video reale o GIF dimostrativa)*

---

## 👨‍💼 Autori

- [Simone Recinelli](https://github.com/SimoneRecinelli) (Matricola S1118757)
- [Diego Santarelli](https://github.com/diegosantarelli) (Matricola S1118746)
- [Andrea Marini](https://github.com/AndreaMarini01) (Matricola S1118778)


---

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.

---
