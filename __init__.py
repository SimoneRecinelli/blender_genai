import bpy
import os
import sys

bl_info = {
    "name": "Blender GenAI Assistant",
    "author": "Simone",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GenAI",
    "description": "AI assistant for modeling via Llama Vision",
    "category": "3D View",
}

addon_path = os.path.dirname(__file__)
modules_path = os.path.join(addon_path, "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)

from . import genai_operator, panel

def register():
    genai_operator.register()
    panel.register()

def unregister():
    panel.unregister()
    genai_operator.unregister()

if __name__ == "__main__":
    register()
