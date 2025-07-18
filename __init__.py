import bpy
import socket

# Import dei file interni all'addon
from . import genai_operator, panel

bl_info = {
    "name": "Blender GenAI Assistant",
    "author": "Simone, Diego, Andrea",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GenAI",
    "description": "AI assistant for modeling via Llama Vision",
    "category": "3D View",
}


def shutdown_gui():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 5055))
        s.sendall(b"shutdown")
        s.close()
        print("[INFO] Comando shutdown inviato alla GUI")
    except Exception as e:
        print(f"[DEBUG] GUI non attiva o errore: {e}")


def monitor_blender_shutdown():
    if not bpy.app.background and not bpy.context.window_manager.windows:
        # Blender sta chiudendo → invia shutdown alla GUI
        shutdown_gui()
        return None  # Non richiama il timer
    return 1.0  # Richiama ogni 1 secondo


def register():
    from . import server

    genai_operator.register()
    panel.register()
    # gui_launcher.register()

    # ✅ Avvia il server Flask
    try:
        # ✅ Avvia il server Flask se non è già avviato
        server.start_flask_server()
        print("[INFO] Server Flask avviato da __init__.py")
    except Exception as e:
        print("[ERRORE] Avvio server Flask:", e)


    bpy.app.timers.register(monitor_blender_shutdown, persistent=True)


def unregister():
    from . import gui_launcher
    shutdown_gui()
    gui_launcher.shutdown_gui()
    panel.unregister()
    genai_operator.unregister()
