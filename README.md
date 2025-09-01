<div align="center">
  <img src="icons/genai_icon.png" alt="Blender GenAI Logo" width="240"/>

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

Sviluppato per il corso di **Computer Graphics & Multimedia** (A.A. 2024/2025) presso l’**Università Politecnica delle Marche**, tenuto dal **Prof. Primo Zingaretti**, coadiuvato dai **Dott. Emanuele Balloni** e [**Dott. Lorenzo Stacchio**](https://github.com/lorenzo-stacchio).

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
  - [📥 Installare l'addon su Blender](#-installare-laddon-su-blender)
  - [🚀 Avviare l'interfaccia](#-avviare-linterfaccia)
- [🪟 Interfaccia del Chatbot](#-interfaccia-esterna-del-chatbot)
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
- 📚 **Sistema RAG** integrato con ricerca semantica nella documentazione Blender
  Sono stati implementati due approcci complementari:  
  1. **RAG basato su JSON tematici** → chunk generati manualmente, con maggiore coerenza semantica e risposte più mirate.  
  2. **RAG basato su parsing PDF** → copertura più ampia e facilmente aggiornabile, utile per domande trasversali sulla documentazione.  

---

## 🧹 Struttura del progetto

```
blender_genai/
├── icons/                        # Icone SVG/PNG per GUI e pannello
├── scripts/                      # Script ausiliari e di test
│   ├── read_pickle.py             # Utility per leggere file pickle
│   ├── blender_chunks.json        # Chunk JSON tematici per RAG
│   ├── Blender_doc.pdf            # Documentazione Blender in formato PDF
│   ├── blender_faiss_index.pkl    # Indice FAISS per il retrieval
│   ├── book_sliced.pdf            # Documento PDF preprocessato in chunk
│   ├── .gitattributes             # Configurazione Git (es. LFS)
│   ├── .gitignore                 # File esclusi dal versionamento
│   └── __init__.py                # Inizializzazione pacchetto scripts
├── extern_gui.py                  # Interfaccia grafica esterna in PyQt5
├── genai_operator.py              # Operatori Blender per interazione con AI
├── gui_launcher.py                # Avvio separato della GUI esterna
├── langchain_rag_blender_pdf.py   # Script RAG basato su documentazione PDF
├── LICENSE                        # Licenza MIT del progetto
├── open_pkl.py                    # Script per aprire file pickle
├── panel.py                       # Pannello UI in Blender (sidebar GenAI)
├── rag_from_json.py                # Script RAG basato su JSON tematico
├── README.md                      # Documentazione principale del progetto
├── server.py                      # Server Flask + gestione dipendenze
├── speech_server.py               # Server Flask per riconoscimento vocale
└── utils.py                       # Funzioni core (RAG, embeddings, AI context)
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

❌ Da controllare
---

## ⚖️ Documentazione Blender (PDF)

Per permettere l'elaborazione della documentazione ufficiale di Blender **in locale**, il repository include il file `book_sliced.pdf`.

## Documentazione Blender (JSON)


❌ DA SCRIVERE E AGGIUNGERE AD INDICE 
---
# ⚙️ Requisiti & Setup

## ✅ Dipendenze Python: installazione automatica
Non è necessario installare manualmente i pacchetti Python:  
le dipendenze vengono installate **automaticamente** tramite gli script inclusi (`.sh` per macOS, `.bat` per Windows).  

Tutti i pacchetti richiesti vengono salvati nella cartella:

```
~/Library/Application Support/Blender/4.5/scripts/modules/     (macOS)
%APPDATA%\Blender Foundation\Blender\4.5\scripts\modules\ (Windows)
```

Dipendenze installate:
- Flask – server locale per gestire richieste
- FAISS – similarity search
- sentence-transformers – embeddings semantici
- LangChain – orchestrazione RAG
- PyMuPDF – parsing PDF
- PyQt5 – interfaccia grafica esterna
- psutil – monitoraggio processi
- requests – API HTTP
- pyttsx3 – sintesi vocale
- SpeechRecognition – dettatura vocale
- sounddevice – input microfono
- openai-whisper – trascrizione audio
- torch – backend Whisper
- scipy – gestione audio
- numpy==1.26.4 – libreria numerica compatibile
- regex – parsing testuale avanzato
- pyobjc – solo macOS
- ffmpeg – eseguibile di sistema, installato automaticamente se assente

---

## 📦 Clonare il repository
Clonare il progetto in locale con:

```bash
git clone https://github.com/SimoneRecinelli/blender_genai.git
cd blender_genai
```

---

## 🛠️ Setup automatico con script

Abbiamo fornito **4 script** che automatizzano l’installazione delle dipendenze:

| Sistema | Script Full | Script Minimal |
|---------|-------------|----------------|
| **macOS** | `setup_env_mac_full.sh` <br> Installa *Homebrew, Git, Python, PyQt5, PortAudio, ffmpeg, Ollama* + dipendenze Python | `setup_env_mac_minimal.sh` <br> Installa solo le dipendenze Python (presuppone che Homebrew, Git, Python siano già presenti) |
| **Windows** | `setup_env_win_full.bat` <br> Installa *Chocolatey, Git, Python, ffmpeg, Ollama* + dipendenze Python | `setup_env_win_minimal.bat` <br> Installa solo le dipendenze Python (presuppone che Git, Python siano già presenti) |

### 🔑 Differenza tra Full e Minimal
- **Full** → pensato per sistemi *vergini*. Installa anche i gestori pacchetti (Homebrew/Chocolatey), Git, Python di sistema, librerie di sistema (PyQt5, PortAudio, ffmpeg), Ollama e i modelli.  
- **Minimal** → pensato per sistemi *già configurati* con i tool principali. Installa solo le dipendenze Python necessarie al plugin e Ollama se assente.

---

## ▶️ Come eseguire gli script

### macOS
1. Apri il terminale e vai nella cartella del progetto:
   ```bash
   cd ~/Desktop/blender_genai
   ```
2. Dai i permessi di esecuzione (solo la prima volta):
   ```bash
   chmod +x setup_env_mac_full.sh
   chmod +x setup_env_mac_minimal.sh
   ```
3. Avvia lo script scelto:
   ```bash
   ./setup_env_mac_full.sh
   ```
   oppure:
   ```bash
   ./setup_env_mac_minimal.sh
   ```

### Windows
1. Apri il **Prompt dei comandi** (`cmd.exe`) come **Amministratore**.  
2. Vai nella cartella del progetto:
   ```bat
   cd Desktop\blender_genai
   ```
3. Esegui lo script scelto:
   ```bat
   setup_env_win_full.bat
   ```
   oppure:
   ```bat
   setup_env_win_minimal.bat
   ```

---

## 🦙 Installare Ollama e scaricare i modelli
Indipendentemente dallo script scelto, è necessario installare Ollama per il proprio sistema operativo:  
➡️ [Scarica Ollama](https://ollama.com/download)

Una volta installato, apri il terminale e scarica i modelli richiesti:

```bash
ollama pull llama3.2-vision
ollama pull llama3:instruct
```

⚠️ Affinché il plugin funzioni correttamente, **Ollama deve essere sempre attivo** sulla macchina!


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

L’addon include una interfaccia grafica personalizzata esterna sviluppata in PyQt5, progettata per offrire un'esperienza utente fluida e moderna, ispirata alle applicazioni di messaggistica. È completamente multi-piattaforma (macOS Apple Silicon e Windows), supporta la cronologia delle conversazioni, invio di immagini della scena Blender, e la modalità dark/light con switch dinamico.

#### ✨ Caratteristiche principali della GUI:

- ✅ Interfaccia separata da Blender, con comunicazione socket asincrona

- 💬 Area di chat con storico persistente e salvataggio automatico

- 🖼️ Supporto per l’invio di screenshot dalla scena Blender

- 🌗 Tema chiaro/scuro attivabile con uno switch animato

- ⌨️ Invio con Enter e a capo con Shift+Invio

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
