bl_info = {
    "name": "Blender GenAI Assistant",
    "author": "Simone",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GenAI",
    "description": "AI assistant for modeling via Llama Vision",
    "category": "3D View",
}

import bpy
from . import genai_operator, panel

def register():
    genai_operator.register()
    panel.register()

def unregister():
    panel.unregister()
    genai_operator.unregister()

if __name__ == "__main__":
    register()

