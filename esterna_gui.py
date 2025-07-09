import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QFileDialog, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer, QSize


class MessageBubble(QLabel):
    def __init__(self, text, sender='user', parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setMargin(10)
        self.setStyleSheet(
            f"QLabel {{ background-color: {'#2d2d2d' if sender == 'user' else '#444'}; color: white; padding: 10px; font-size: 14px; border-radius: 10px; }}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)



class ChatTextBox(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            if not self.parent.attesa_risposta:
                self.parent.invia_domanda()
        else:
            super().keyPressEvent(event)


class GenAIClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GenAI Assistant Chat")
        self.setGeometry(100, 100, 600, 500)
        self.attesa_risposta = False

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
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: white;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollArea {
                border: none;
            }
        """)

        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.chat_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_content)

        self.textbox = ChatTextBox(self)
        self.textbox.setFixedHeight(60)
        self.textbox.setPlaceholderText("Scrivi una domanda...")

        self.add_image_button = QPushButton()
        self.add_image_button.setIcon(QIcon("load.svg"))
        self.add_image_button.setIconSize(QSize(24, 24))
        self.add_image_button.setFixedSize(40, 40)
        self.add_image_button.setStyleSheet("QPushButton { border-radius: 20px; background-color: white; }")
        self.add_image_button.clicked.connect(self.carica_immagine)

        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("send.svg"))
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setFixedSize(40, 40)
        self.send_button.setStyleSheet("QPushButton { border-radius: 20px; background-color: white; }")
        self.send_button.clicked.connect(self.invia_domanda)

        self.preview_widget = QWidget()
        self.preview_layout = QHBoxLayout()
        self.preview_layout.setContentsMargins(10, 5, 10, 5)
        self.preview_widget.setLayout(self.preview_layout)

        self.input_layout = QHBoxLayout()
        self.input_layout.setSpacing(10)
        self.input_layout.addWidget(self.add_image_button)
        self.input_layout.addWidget(self.textbox)
        self.input_layout.addWidget(self.send_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.preview_widget)
        self.main_layout.addLayout(self.input_layout)
        self.setLayout(self.main_layout)

        self.image_path = None
        self.image_preview_label = None
        self.delete_button = None
        self.image_container = None
        self.loading_label = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_response)

        self.bubbles = []  # Bubble list per il resize

    def add_message(self, text, sender='user'):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        if sender == 'user' and self.image_path:
            img_label = QLabel()
            img_label.setPixmap(QPixmap(self.image_path).scaledToWidth(150, Qt.SmoothTransformation))
            img_wrapper = QHBoxLayout()
            img_wrapper.addStretch()
            img_wrapper.addWidget(img_label)
            layout.addLayout(img_wrapper)

        bubble = MessageBubble(text, sender, self)
        bubble.setMaximumWidth(int(self.width() * 0.85))
        if sender == 'user':
            bubble.setMinimumWidth(150)
            bubble.setAlignment(Qt.AlignRight)
        else:
            bubble.setAlignment(Qt.AlignLeft)
        self.bubbles.append(bubble)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if sender == 'user':
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        bubble_wrap = QWidget()
        bubble_wrap.setLayout(wrapper)
        layout.addWidget(bubble_wrap)

        container.setLayout(layout)
        self.chat_layout.addWidget(container)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

        if sender == 'user' and self.image_container:
            self.image_container.deleteLater()
            self.image_container = None
            self.image_preview_label = None
            self.delete_button = None
            self.image_path = None

    def invia_domanda(self):
        domanda = self.textbox.toPlainText().strip()
        if not domanda or self.attesa_risposta:
            return

        self.attesa_risposta = True
        self.send_button.setEnabled(False)
        self.add_message(domanda, 'user')
        self.textbox.clear()

        self.loading_label = QLabel()
        movie = QMovie("loading.gif")
        self.loading_label.setMovie(movie)
        movie.start()
        self.chat_layout.addWidget(self.loading_label)

        try:
            payload = {"question": domanda}
            if self.image_path:
                payload["image_path"] = self.image_path

            r = requests.post("http://127.0.0.1:5000/ask", json=payload)
            if r.status_code == 200:
                self.timer.start(2000)
            else:
                self.loading_label.hide()
                self.add_message("❌ Errore nella richiesta a Blender.", 'bot')
                self.send_button.setEnabled(True)
                self.attesa_risposta = False
        except Exception as e:
            self.loading_label.hide()
            self.add_message(f"❌ Errore: {str(e)}", 'bot')
            self.send_button.setEnabled(True)
            self.attesa_risposta = False

    def check_response(self):
        try:
            r = requests.get("http://127.0.0.1:5000/response")
            if r.status_code != 200:
                return
            data = r.json()
            if data["status"] == "ready":
                self.timer.stop()
                if self.loading_label:
                    self.loading_label.hide()
                self.send_button.setEnabled(True)
                self.attesa_risposta = False
                self.add_message(data["response"], 'bot')
        except Exception as e:
            if self.loading_label:
                self.loading_label.hide()
            self.send_button.setEnabled(True)
            self.attesa_risposta = False
            self.add_message(f"❌ Errore: {str(e)}", 'bot')

    def carica_immagine(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona immagine", "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path = file_path

            for i in reversed(range(self.preview_layout.count())):
                widget = self.preview_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            self.image_preview_label = QLabel()
            pixmap = QPixmap(file_path).scaledToWidth(100, Qt.SmoothTransformation)
            self.image_preview_label.setPixmap(pixmap)

            self.delete_button = QPushButton()
            self.delete_button.setIcon(QIcon("trash.svg"))
            self.delete_button.setIconSize(QSize(20, 20))
            self.delete_button.setFixedSize(28, 28)
            self.delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #c00;
                }
            """)
            self.delete_button.clicked.connect(self.rimuovi_immagine)

            container = QWidget()
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(6)
            h_layout.addWidget(self.image_preview_label)
            h_layout.addWidget(self.delete_button)
            container.setLayout(h_layout)

            self.image_container = container
            self.preview_layout.addWidget(container)

    def rimuovi_immagine(self):
        self.image_path = None
        if self.image_container:
            self.image_container.deleteLater()
        self.image_container = None
        self.image_preview_label = None
        self.delete_button = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for bubble in self.bubbles:
            bubble.setMaximumWidth(int(self.width() * 0.6))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GenAIClient()
    win.show()
    sys.exit(app.exec_())