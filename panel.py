import bpy

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
    chat_history: bpy.props.CollectionProperty(type=GenAIChatEntry)

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

        # Storico visivo tipo chat
        chat_box = layout.box()
        chat_box.label(text="🧠 Chat:")
        for entry in props.chat_history[-20:]:  # mostra ultimi 20 messaggi
            box = chat_box.box()
            icon = 'USER' if entry.sender == 'USER' else 'COMMUNITY'
            box.label(text=entry.sender + ":", icon=icon)

            if entry.sender == 'USER':
                box.label(text=entry.message)
            else:
                op = box.operator("genai.open_response", text="🧠 Apri nel Text Editor")
                op.message = entry.message


        layout.separator()

        # Input utente in fondo
        input_box = layout.box()
        input_box.prop(props, "genai_question", text="Scrivi la tua domanda")
        input_box.operator("genai.ask_operator", text="📤 Invia")
        layout.operator("genai.open_text_editor", text="📝 Apri risposta nel Text Editor")

'''
class GENAI_OT_ShowMessage(bpy.types.Operator):
    bl_idname = "genai.show_message"
    bl_label = "Messaggio completo"

    message: bpy.props.StringProperty()

    def draw(self, context):
        col = self.layout.column()
        for line in self.message.split("\n"):
            col.label(text=line)

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
'''

# Pannello laterale in Text Editor con risposta completa scrollabile
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
    bl_description = "Apre la risposta completa nel Text Editor nella finestra corrente"

    def execute(self, context):
        name = "MessaggioCompletoGenAI"
        if name not in bpy.data.texts:
            text_block = bpy.data.texts.new(name)
        else:
            text_block = bpy.data.texts[name]

        # Cerca un'area di tipo TEXT_EDITOR
        for area in context.window.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR':
                        space.text = text_block
                        self.report({'INFO'}, "Risposta aperta nel Text Editor.")
                        return {'FINISHED'}
        self.report({'WARNING'}, "Nessuna area Text Editor trovata. Aprine una manualmente.")
        return {'CANCELLED'}


# Registrazione classi
classes = [
    GenAIChatEntry,
    GenAIProperties,
    GENAI_PT_Panel,
    GENAI_PT_FullResponsePanel,
    GENAI_OT_OpenTextEditor,
    GENAI_OT_OpenResponseInEditor
    #GENAI_OT_ShowMessage
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.genai_props


