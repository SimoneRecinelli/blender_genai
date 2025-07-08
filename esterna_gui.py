import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize



from PyQt5.QtCore import QSize

class MessageBubble(QLabel):
    def __init__(self, text, sender='user', parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setMargin(10)

        self.setStyleSheet(
            f"""
            QLabel {{
                border-radius: 10px;
                background-color: {"#2d2d2d" if sender == "user" else "#444"};
                color: white;
                padding: 10px;
                font-size: 14px;
            }}
            """
            
        )
        # Si adatta dinamicamente, ma non supera il 70% della finestra
        #self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        if sender == 'user':
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


        #self.setMaximumWidth(int(parent.width() * 0.7) if parent else 400)


class GenAIClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GenAI Assistant Chat")
        self.setGeometry(100, 100, 600, 500)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-family: Arial;
                font-size: 13px;
            }
            QTextEdit {
                background-color: #2e2e2e;
                color: white;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 8px;
            }F
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
                border-radius: 3px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }

        """)

        # Chat layout
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.chat_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_content)

        # Input layout con icone
        self.textbox = QTextEdit()
        self.textbox.setFixedHeight(60)
        self.textbox.setPlaceholderText("Scrivi una domanda...")

        # === Pulsante "+" ===
        self.add_image_button = QPushButton()
        self.add_image_button.setIcon(QIcon("plus.png"))
        self.add_image_button.setIconSize(QSize(24, 24))
        self.add_image_button.setFixedSize(40, 40)
        self.add_image_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: white;
            }
        """)
        self.add_image_button.clicked.connect(self.carica_immagine)

        # === Pulsante "invia" ===
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("paperplane.png"))
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setFixedSize(40, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: white;
            }
        """)
        self.send_button.clicked.connect(self.invia_domanda)

        # Componi layout input
        self.input_layout = QHBoxLayout()
        self.input_layout.setSpacing(10)
        self.input_layout.addWidget(self.add_image_button)
        self.input_layout.addWidget(self.textbox)
        self.input_layout.addWidget(self.send_button)


        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(self.input_layout)


        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_response)

        self.last_question = ""
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        max_width = int(self.width() * 0.7)
        for i in range(self.chat_layout.count()):
            container = self.chat_layout.itemAt(i).widget()
            if container:
                layout = container.layout()
                if layout:
                    for j in range(layout.count()):
                        bubble = layout.itemAt(j).widget()
                        if isinstance(bubble, MessageBubble):
                            bubble.setMaximumWidth(max_width)

    '''
    def add_message(self, text, sender='user'):
        bubble = MessageBubble(text, sender, self)
        bubble.setMaximumWidth(int(self.width() * 0.7))

        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(10, 5, 10, 5)

        if sender == 'user':
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()

        container_widget = QWidget()
        container_widget.setLayout(container_layout)
        self.chat_layout.addWidget(container_widget)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))
    '''

    def add_message(self, text, sender='user'):
        bubble = MessageBubble(text, sender, self)

        # Contenitore per forzare larghezza + allineamento
        bubble_wrapper = QWidget()
        bubble_wrapper_layout = QHBoxLayout()
        bubble_wrapper_layout.setContentsMargins(0, 0, 0, 0)

        if sender == 'user':
            bubble_wrapper_layout.addStretch()
            bubble_wrapper_layout.addWidget(bubble)
        else:
            bubble_wrapper_layout.addWidget(bubble)
            bubble_wrapper_layout.addStretch()

        bubble_wrapper.setLayout(bubble_wrapper_layout)

        # Padding verticale e margini
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 5, 10, 5)
        container_layout.addWidget(bubble_wrapper)
        container.setLayout(container_layout)

        self.chat_layout.addWidget(container)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))


    '''
    def invia_domanda(self):
        domanda = self.textbox.toPlainText().strip()
        if not domanda:
            return
        self.last_question = domanda
        self.add_message(domanda, 'user')
        self.textbox.clear()

        try:
            r = requests.post("http://127.0.0.1:5000/ask", json={"question": domanda})
            if r.status_code == 200:
                self.timer.start(2000)
            else:
                self.add_message("❌ Errore nella richiesta a Blender.", 'bot')
        except Exception as e:
            self.add_message(f"❌ Errore: {str(e)}", 'bot')
    '''

    def invia_domanda(self):
        domanda = self.textbox.toPlainText().strip()
        if not domanda:
            return

        self.last_question = domanda
        self.add_message(domanda, 'user')
        self.textbox.clear()

        try:
            payload = {"question": domanda}
            if hasattr(self, "image_path"):
                payload["image_path"] = self.image_path

            r = requests.post("http://127.0.0.1:5000/ask", json=payload)
            if r.status_code == 200:
                self.timer.start(2000)
            else:
                self.add_message("❌ Errore nella richiesta a Blender.", 'bot')
        except Exception as e:
            self.add_message(f"❌ Errore: {str(e)}", 'bot')


    def check_response(self):
        try:
            r = requests.get("http://127.0.0.1:5000/response")
            if r.status_code != 200:
                return
            data = r.json()
            if data["status"] == "ready":
                self.timer.stop()
                self.add_message(data["response"], 'bot')
        except Exception as e:
            self.add_message(f"❌ Errore: {str(e)}", 'bot')

    def carica_immagine(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona immagine", "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.add_message(f"📷 Immagine caricata: {file_path.split('/')[-1]}", 'user')
            # eventualmente puoi salvarla in una variabile globale:
            self.image_path = file_path


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GenAIClient()
    win.show()
    sys.exit(app.exec_())
