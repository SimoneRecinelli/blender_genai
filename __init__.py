bl_info = {
    "name": "GenAI Assistant",
    "author": "Simone",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "description": "Assistente AI per la modellazione con LLaVA",
    "category": "3D View"
}

from . import panel, operator

def register():
    panel.register()
    operator.register()

def unregister():
    panel.unregister()
    operator.unregister()
