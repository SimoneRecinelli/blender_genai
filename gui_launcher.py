import os
import subprocess
import sys
import bpy

class GENAI_OT_ShowExternalChat(bpy.types.Operator):
    bl_idname = "genai.show_external_chat"
    bl_label = "Apri Chat Esterna"

    def execute(self, context):
        blender_python = sys.executable
        gui_path = os.path.join(os.path.dirname(__file__), "extern_gui.py")

        try:
            subprocess.Popen([blender_python, gui_path])
            self.report({'INFO'}, "✅ Chat esterna avviata.")
        except Exception as e:
            self.report({'ERROR'}, f"Errore GUI: {str(e)}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(GENAI_OT_ShowExternalChat)

def unregister():
    bpy.utils.unregister_class(GENAI_OT_ShowExternalChat)
