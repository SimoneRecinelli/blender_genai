import bpy
# Import dei file interni all'addon
from . import genai_operator, panel, gui_launcher

bl_info = {
    "name": "Blender GenAI Assistant",
    "author": "Simone, Diego, Andrea",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GenAI",
    "description": "AI assistant for modeling via Llama Vision",
    "category": "3D View",
}

def register():
    from . import server

    genai_operator.register()
    panel.register()
    gui_launcher.register()

    # ✅ Avvia il server Flask
    try:
        # ✅ Avvia il server Flask se non è già avviato
        server.start_flask_server()
        print("[INFO] Server Flask avviato da __init__.py")
    except Exception as e:
        print("[ERRORE] Avvio server Flask:", e)



def unregister():
    gui_launcher.unregister()
    panel.unregister()
    genai_operator.unregister()
