import bpy
import subprocess
import sys
import os

class GENAI_OT_InstallDeps(bpy.types.Operator):
    bl_idname = "genai.install_deps"
    bl_label = "Installa Dipendenze"
    bl_description = "Installa i pacchetti richiesti per l'assistente GenAI"

    def execute(self, context):
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "faiss-cpu", "sentence-transformers", "bs4"
            ])

            # Mostra popup al termine
            def draw(self, context):
                self.layout.label(text="Dipendenze installate correttamente.")

            bpy.context.window_manager.popup_menu(draw, title="Installazione completata", icon='CHECKMARK')

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Errore: {e}")
            return {'CANCELLED'}
    
    # Operatore: aggiorna indice FAISS
class GENAI_OT_BuildIndex(bpy.types.Operator):
    bl_idname = "genai.build_index"
    bl_label = "Aggiorna Documentazione"
    bl_description = "Ricostruisce l’indice FAISS a partire dalla documentazione HTML"

    def execute(self, context):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "build_blender_index.py")
            if not os.path.exists(script_path):
                self.report({'ERROR'}, "File 'build_blender_index.py' non trovato.")
                return {'CANCELLED'}

            # Esecuzione script
            subprocess.check_call([sys.executable, script_path])

            # Mostra popup al termine
            def draw(self, context):
                self.layout.label(text="RAG terminato. Indice aggiornato correttamente.")

            bpy.context.window_manager.popup_menu(draw, title="Indicizzazione completata", icon='INFO')

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Errore durante l'aggiornamento: {e}")
            return {'CANCELLED'}

# Registrazione
classes = [
    GENAI_OT_InstallDeps,
    GENAI_OT_BuildIndex,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
