import bpy

def get_model_context():
    selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

    if not selected_objs:
        return "Nessun oggetto mesh selezionato nella scena."

    context_list = []
    for obj in selected_objs:
        mesh = obj.data
        context = {
            "Nome oggetto": obj.name,
            "Vertici": len(mesh.vertices),
            "Spigoli": len(mesh.edges),
            "Facce": len(mesh.polygons),
            "Modificatori": [m.name for m in obj.modifiers] or ["Nessuno"]
        }
        obj_summary = "\n".join([f"{k}: {v}" for k, v in context.items()])
        context_list.append(obj_summary)

    header = f"Hai selezionato {len(selected_objs)} oggetto/i. Ecco i dettagli:\n"
    return header + "\n\n".join(context_list)


import subprocess

def query_ollama(prompt):
    #print(f"[DEBUG] query_ollama ricevuto prompt: {prompt!r}")
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:latest"],  # usa il modello corretto
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        #print(f"[DEBUG] Output Ollama: {result.stdout!r}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] CalledProcessError: {e.stderr}")
        return f"Errore nella chiamata Ollama: {e.stderr}"
    except Exception as e:
        print(f"[ERROR] Errore generico: {e}")
        return f"Errore generico: {e}"

