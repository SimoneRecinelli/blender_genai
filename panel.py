import bpy
import subprocess
import os
import sys

# ✅ Proprietà necessarie per la comunicazione
class GenAIChatEntry(bpy.types.PropertyGroup):
    sender: bpy.props.EnumProperty(
        name="Sender",
        items=[
            ('USER', "Utente", "Messaggio inviato"),
            ('AI', "GenAI", "Risposta ricevuta")
        ]
    )
    message: bpy.props.StringProperty(name="Messaggio")

class GenAIProperties(bpy.types.PropertyGroup):
    genai_question: bpy.props.StringProperty(name="Domanda", default="")
    genai_response: bpy.props.StringProperty(name="Risposta", default="")
    genai_response_text: bpy.props.StringProperty(name="Risposta completa", default="")
    chat_history: bpy.props.CollectionProperty(type=GenAIChatEntry)
    genai_image_path: bpy.props.StringProperty(name="Percorso immagine", subtype='FILE_PATH')
    genai_status: bpy.props.StringProperty(name="Stato", default="")

# ✅ Solo il bottone visivo per aprire la GUI
class GENAI_PT_Panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        layout.operator("genai.show_external_chat", text="Apri Chat Esterna 🖥️", icon="PLUGIN")
        layout.separator()
        layout.operator("genai.run_rag", text="Esegui RAG da JSON 📄", icon="FILE_SCRIPT")
        layout.operator("genai.run_rag_pdf", text="Esegui RAG da PDF 📄", icon="FILE_SCRIPT")

class GENAI_OT_ShowExternalChat(bpy.types.Operator):
    bl_idname = "genai.show_external_chat"
    bl_label = "Apri Chat Esterna"
    bl_description = "Avvia o porta in primo piano la finestra della chat GenAI esterna"

    def execute(self, context):
        import socket
        script_path = os.path.join(os.path.dirname(__file__), "extern_gui.py")

        # 🔎 Verifica se la GUI è già attiva (socket 5055)
        try:
            s = socket.create_connection(("localhost", 5055), timeout=1)
            s.sendall(b"bring-to-front")
            s.close()
            self.report({'INFO'}, "Chat già attiva → portata in primo piano.")
            return {'FINISHED'}
        except (ConnectionRefusedError, OSError):
            pass  # nessuna GUI attiva, avvia nuova istanza

        # 🟢 Avvia GUI in processo separato
        try:
            subprocess.Popen(
                [sys.executable, script_path],

            )
            self.report({'INFO'}, "Chat avviata.")
        except Exception as e:
            self.report({'ERROR'}, f"Errore avvio GUI: {e}")
        return {'FINISHED'}

class GENAI_OT_RunRAG(bpy.types.Operator):
    bl_idname = "genai.run_rag"
    bl_label = "Esegui RAG"
    bl_description = "Esegui il sistema RAG per interrogare la documentazione di Blender"

    def execute(self, context):
        script_path = os.path.join(os.path.dirname(__file__), "rag_from_json.py")
        try:
            subprocess.run([sys.executable, script_path], check=True)
            self.report({'INFO'}, "RAG da JSON eseguito con successo.")
        except Exception as e:
            self.report({'ERROR'}, f"Errore durante l'esecuzione RAG: {e}")
        return {'FINISHED'}

class GENAI_OT_RunRAGpdf(bpy.types.Operator):
    bl_idname = "genai.run_rag_pdf"
    bl_label = "Esegui RAG"
    bl_description = "Esegui il sistema RAG per interrogare la documentazione di Blender"

    def execute(self, context):
        script_path = os.path.join(os.path.dirname(__file__), "langchain_rag_blender_pdf.py")
        try:
            subprocess.run([sys.executable, script_path], check=True)
            self.report({'INFO'}, "RAG da PDF eseguito con successo.")
        except Exception as e:
            self.report({'ERROR'}, f"Errore durante l'esecuzione RAG: {e}")
        return {'FINISHED'}


# ✅ Registrazione di tutte le classi
classes = [
    GenAIChatEntry,
    GenAIProperties,
    GENAI_PT_Panel,
    GENAI_OT_RunRAG,
    GENAI_OT_RunRAGpdf,
    GENAI_OT_ShowExternalChat,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.genai_props

