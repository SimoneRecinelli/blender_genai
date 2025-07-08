import bpy
# Import dei file interni all'addon
from . import genai_operator, panel, install_operator

bl_info = {
    "name": "Blender GenAI Assistant",
    "author": "Simone",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GenAI",
    "description": "AI assistant for modeling via Llama Vision",
    "category": "3D View",
}

def register():
    genai_operator.register()
    panel.register()
    install_operator.register()

    # ✅ Avvia il server Flask
    try:
        from . import server
        server.start_flask_server()
        print("[DEBUG] Server Flask avviato su http://localhost:5000")
    except Exception as e:
        print("[ERRORE] Avvio server Flask:", e)


def unregister():
    install_operator.unregister()  # ✅ unregister dell’operatore
    panel.unregister()
    genai_operator.unregister()

if __name__ == "__main__":
    register()
