import os
import sys
import socket
import subprocess
import platform

def bring_window_to_front():
    try:
        with socket.create_connection(("localhost", 5055), timeout=1) as s:
            s.sendall(b"bring-to-front")
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False

def launch_gui_if_not_running():
    if bring_window_to_front():
        return

    # Lancia GUI solo se non attiva
    gui_path = os.path.join(os.path.dirname(__file__), "extern_gui.py")
    python_exe = sys.executable

    kwargs = {
        "args": [python_exe, gui_path],
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    subprocess.Popen(**kwargs)

def shutdown_gui():
    try:
        with socket.create_connection(("localhost", 5055), timeout=1) as s:
            s.sendall(b"shutdown")
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False

