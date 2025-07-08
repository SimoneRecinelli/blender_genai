import bpy
import subprocess
import sys
import os

class GENAI_OT_InstallDeps(bpy.types.Operator):
    bl_idname = "genai.install_deps"
    bl_label = "Installa dipendenze GenAI"

    def execute(self, context):
        blender_python = sys.executable

        packages = [
            "requests",
            "flask",
            "faiss-cpu",
            "sentence-transformers"
        ]

        success = True

        for package in packages:
            try:
                subprocess.check_call([blender_python, "-m", "pip", "install", package])
            except subprocess.CalledProcessError:
                self.report({'ERROR'}, f"Errore nell’installazione di {package}")
                success = False

        if success:
            self.report({'INFO'}, "✅ Dipendenze installate correttamente.")
        return {'FINISHED'}
    
    # 📚 Operatore: aggiorna indice FAISS
class GENAI_OT_BuildIndex(bpy.types.Operator):
    bl_idname = "genai.build_index"
    bl_label = "📚 Aggiorna Documentazione"
    bl_description = "Ricostruisce l’indice FAISS a partire dalla documentazione HTML"

    def execute(self, context):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "build_blender_index.py")
            if not os.path.exists(script_path):
                self.report({'ERROR'}, "⚠️ File 'build_blender_index.py' non trovato.")
                return {'CANCELLED'}

            subprocess.check_call([sys.executable, script_path])
            self.report({'INFO'}, "✅ Indice aggiornato correttamente.")
        except Exception as e:
            self.report({'ERROR'}, f"❌ Errore durante l'aggiornamento: {e}")
        return {'FINISHED'}

# 🔧 Registrazione
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
