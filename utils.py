import bpy
import bmesh
import subprocess
import os
from bs4 import BeautifulSoup

def build_conversational_context(props):
    history_lines = []
    for entry in props.chat_history:
        prefix = "Utente" if entry.sender == 'USER' else "GenAI"
        history_lines.append(f"{prefix}: {entry.message}")
    return "\n".join(history_lines)


# ===================== PARTE 1 – CONTEXT MODELLO BLENDER =====================
# Prova commento

def get_model_context():
    selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not selected_objs:
        return "Nessun oggetto mesh selezionato nella scena."

    context_list = []
    for obj in selected_objs:
        mesh = obj.data
        dimensions = obj.dimensions
        materials = [slot.material.name if slot.material else "Nessuno" for slot in obj.material_slots]
        uv_layers = list(mesh.uv_layers.keys()) or ["Nessuna"]
        modifiers = [m.type for m in obj.modifiers] or ["Nessuno"]
        shading = "Smooth" if any(p.use_smooth for p in mesh.polygons) else "Flat"
        parent_name = obj.parent.name if obj.parent else "Nessuno"

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        num_tris = sum(1 for f in bm.faces if len(f.verts) == 3)
        is_manifold = all(e.is_manifold for e in bm.edges)
        double_verts = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0001)["targetmap"]
        flipped_normals = sum(1 for f in bm.faces if f.normal.z < 0)

        bm.free()

        context = {
            "Nome oggetto": obj.name,
            "Vertici": len(mesh.vertices),
            "Spigoli": len(mesh.edges),
            "Facce": len(mesh.polygons),
            "Triangoli": num_tris,
            "Dimensioni (X,Y,Z)": f"{dimensions.x:.2f}, {dimensions.y:.2f}, {dimensions.z:.2f}",
            "Modificatori": modifiers,
            "Materiali": materials,
            "UV Maps": uv_layers,
            "Shading": shading,
            "Parent": parent_name,
            "Manifold": "Sì" if is_manifold else "No",
            "Vertici doppi (vicini)": len(double_verts),
            "Facce con normali invertite (Z-)": flipped_normals
        }

        summary = "\n".join([f"{k}: {v}" for k, v in context.items()])
        context_list.append(summary)

    header = f"Hai selezionato {len(selected_objs)} oggetto/i. Ecco i dettagli:\n"
    return header + "\n\n".join(context_list)

# ===================== PARTE 2 – ESTRAZIONE DOCUMENTAZIONE =====================

def estrai_testo_da_html(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
        return soup.get_text(separator="\n")

def costruisci_blender_docs(carp_html_folder, output_txt):
    tutto_il_testo = ""
    for root, _, files in os.walk(carp_html_folder):
        for file in files:
            if file.endswith(".html"):
                path_file = os.path.join(root, file)
                try:
                    testo = estrai_testo_da_html(path_file)
                    tutto_il_testo += f"\n\n--- {file} ---\n{testo}"
                except Exception as e:
                    print(f"[ERRORE] File {file}: {e}")

    try:
        with open(output_txt, "w", encoding="utf-8") as out:
            out.write(tutto_il_testo)
        print(f"[INFO] File della documentazione salvato in: {output_txt}")
    except Exception as e:
        print(f"[ERRORE] Scrittura file: {e}")


# ===================== PARTE 3 – QUERY OLLAMA CON DOCUMENTAZIONE =====================

def query_ollama_with_docs(user_question, path_to_docs="blender_docs.txt", props=None):
    print("[DEBUG] Esecuzione query_ollama_with_docs")

    model_context = get_model_context()
    chat_history = build_conversational_context(props) if props else ""
    print("[DEBUG] Cronologia passata al modello:\n", chat_history)
    print("[DEBUG] Contesto modello ottenuto")

    try:
        with open(path_to_docs, "r", encoding="utf-8") as f:
            blender_docs = f.read()
        print("[DEBUG] Documentazione letta con successo")
    except FileNotFoundError:
        blender_docs = "Documentazione non disponibile."
        print("[DEBUG] Documentazione NON trovata")

    prompt = (
        "Rispondi basandoti **prima di tutto** sulla documentazione ufficiale di Blender.\n"
        "Puoi anche tenere conto della **cronologia della conversazione** per rispondere meglio, se utile.\n"
        "Se la risposta non è nella documentazione ma è deducibile dal contesto della conversazione, puoi comunque rispondere.\n"
        "Se non trovi nulla né nella documentazione né nella conversazione, **dillo chiaramente**.\n\n"
        "Se la risposta non è presente, **dillo esplicitamente**.\n\n"
        "=== Documentazione Ufficiale Blender ===\n"
        f"{blender_docs[:1000]}...\n\n"
        "=== Contesto Modello nella Scena ===\n"
        f"{model_context}\n\n"
        "=== Cronologia conversazione ===\n"
        f"{chat_history}\n\n"
        f"=== Domanda utente ===\n{user_question}\n\n"
        "Rispondi in italiano."
    )


    print("[DEBUG] Prompt costruito (lunghezza:", len(prompt), "caratteri)")

    try:
        result = subprocess.run(
            ["/usr/local/bin/ollama", "run", "deepseek-r1"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        print("[DEBUG] Chiamata Ollama eseguita")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Ollama ha restituito errore: {e.stderr}")
        return f"[Errore Ollama] {e.stderr}"
    except Exception as e:
        print(f"[ERRORE] Generico: {e}")
        return f"[Errore generico] {str(e)}"

# ===================== ESEMPIO USO =====================

if __name__ == "__main__":
    # Costruzione documentazione una volta sola (decommenta solo la prima volta)
    costruisci_blender_docs("/Users/andreamarini/Desktop/blender_genai/blender_manual_v440_en.html", "blender_docs.txt")

    # Esegui una domanda all’AI
    risposta = query_ollama_with_docs("Come posso applicare un modificatore booleano a questo oggetto?")
    print(risposta)
