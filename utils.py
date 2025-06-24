import requests

def query_llava(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llava",
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json().get("response", "Nessuna risposta.")
    except Exception as e:
        return f"Errore: {str(e)}"
