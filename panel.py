import bpy
import os

# Ogni messaggio nella chat
class GenAIChatEntry(bpy.types.PropertyGroup):
    sender: bpy.props.EnumProperty(
        name="Sender",
        items=[
            ('USER', "Utente", "Messaggio inviato"),
            ('AI', "GenAI", "Risposta ricevuta")
        ]
    )
    message: bpy.props.StringProperty(name="Messaggio")

# Proprietà della scena
class GenAIProperties(bpy.types.PropertyGroup):
    genai_question: bpy.props.StringProperty(name="Domanda", default="")
    genai_response: bpy.props.StringProperty(name="Risposta", default="")
    genai_response_text: bpy.props.StringProperty(name="Risposta completa", default="")
    chat_history: bpy.props.CollectionProperty(type=GenAIChatEntry)
    genai_image_path: bpy.props.StringProperty(name="Percorso immagine", subtype='FILE_PATH')
    genai_status: bpy.props.StringProperty(name="Stato", default="")

# Pannello laterale in Blender
class GENAI_PT_Panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.genai_props

        # Storico chat
        chat_box = layout.box()
        chat_box.label(text="🧠 Chat:")
        for entry in props.chat_history[-20:]:
            box = chat_box.box()
            icon = 'USER' if entry.sender == 'USER' else 'COMMUNITY'
            box.label(text=entry.sender + ":", icon=icon)
            if entry.sender == 'USER':
                box.label(text=entry.message)
            else:
                op = box.operator("genai.open_response", text="🧠 Apri nel Text Editor")
                op.message = entry.message

        layout.separator()

        # Input e bottoni
        input_box = layout.box()
        input_box.prop(props, "genai_question", text="Scrivi la tua domanda")

        row = input_box.row(align=True)
        row.operator("genai.ask_operator", text="📤 Invia")
        row.operator("genai.load_image", text="📷 Carica Immagine")

        # ✅ Mostra stato (es: immagine caricata)
        if props.genai_status:
            input_box.label(text=props.genai_status, icon='INFO')

class GENAI_PT_FullResponsePanel(bpy.types.Panel):
    bl_label = "Risposta completa"
    bl_idname = "GENAI_PT_full_response_panel"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.genai_props
        layout.label(text="Ultima risposta generata:")
        layout.prop(props, "genai_response", text="")

class GENAI_OT_OpenResponseInEditor(bpy.types.Operator):
    bl_idname = "genai.open_response"
    bl_label = "Apri risposta AI"

    message: bpy.props.StringProperty()

    def execute(self, context):
        name = "MessaggioCompletoGenAI.txt"
        text_block = bpy.data.texts.get(name) or bpy.data.texts.new(name)
        text_block.clear()
        text_block.write(self.message)

        area = context.area
        area.type = 'TEXT_EDITOR'
        for space in area.spaces:
            if space.type == 'TEXT_EDITOR':
                space.text = text_block
                break
        return {'FINISHED'}

class GENAI_OT_OpenTextEditor(bpy.types.Operator):
    bl_idname = "genai.open_text_editor"
    bl_label = "Apri Text Editor con risposta"

    def execute(self, context):
        name = "MessaggioCompletoGenAI"
        if name not in bpy.data.texts:
            text_block = bpy.data.texts.new(name)
        else:
            text_block = bpy.data.texts[name]

        for area in context.window.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR':
                        space.text = text_block
                        self.report({'INFO'}, "Risposta aperta nel Text Editor.")
                        return {'FINISHED'}
        self.report({'WARNING'}, "Nessuna area Text Editor trovata.")
        return {'CANCELLED'}

# Registrazione classi
classes = [
    GenAIChatEntry,
    GenAIProperties,
    GENAI_PT_Panel,
    GENAI_PT_FullResponsePanel,
    GENAI_OT_OpenTextEditor,
    GENAI_OT_OpenResponseInEditor
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.genai_props
