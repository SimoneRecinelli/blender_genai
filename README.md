# 🧠 Blender GenAI Assistant

Questo repository contiene un addon per Blender che integra un assistente AI basato su LLM, capace di rispondere a domande tecniche e contestuali grazie a un sistema RAG (Retrieval-Augmented Generation).

## 📄 Documentazione Blender (PDF)

Per permettere l'elaborazione della documentazione di Blender **in locale** tramite RAG, viene incluso in questo repository il file `Blender_doc.pdf`, un manuale completo in formato PDF.

⚠️ **Attenzione**: questo file è gestito tramite **Git LFS** (Large File Storage), poiché supera il limite di 100MB imposto da GitHub.

---

## ⚙️ Requisiti

### 1. Installare Git LFS

Se non lo hai già, esegui i seguenti comandi **PRIMA di clonare** il repository:

```bash
# Su macOS (Homebrew)
brew install git-lfs

# Su Ubuntu/Debian
sudo apt install git-lfs

# Inizializzazione globale
git lfs install
```

### 2. Clonare la repository
```bash
git clone https://github.com/tuo-utente/blender_genai.git
```

### 3. Per chi ha già clonato senza LFS
Se hai già eseguito il clone senza Git LFS installato, puoi recuperare i file mancanti con:
```bash
git lfs install
git lfs pull
```

