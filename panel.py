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
            row = chat_box.row()
            icon = 'USER' if entry.sender == 'USER' else 'COMMUNITY'
            row.label(text=entry.sender + ":", icon=icon)
            row.operator("genai.show_message", text="📰 Mostra").message = entry.message


        layout.separator()

        # Input utente in fondo
        input_box = layout.box()
        input_box.prop(props, "genai_question", text="Scrivi la tua domanda")
        input_box.operator("genai.ask_operator", text="📤 Invia")

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


# Registrazione classi
classes = [
    GenAIChatEntry,
    GenAIProperties,
    GENAI_PT_Panel,
    GENAI_OT_ShowMessage
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.genai_props


