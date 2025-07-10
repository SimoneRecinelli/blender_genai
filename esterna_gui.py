import sys
import os
import platform
import requests
from ctypes import c_void_p
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QFileDialog
)
from PyQt5.QtGui import QIcon, QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer, QSize

if platform.system() == "Darwin":
    import objc
    from objc import pyobjc_id
    from AppKit import NSApplication, NSWindow, NSPopUpMenuWindowLevel

qt_app = None
chat_window = None
ICON_PATH = lambda name: os.path.join(os.path.dirname(__file__), name)

class MessageBubble(QLabel):
    def __init__(self, text, sender='user', parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setMargin(10)
        self.setStyleSheet(
            f"QLabel {{ background-color: {'#2d2d2d' if sender == 'user' else '#444'}; color: white; padding: 10px; font-size: 14px; border-radius: 10px; }}"
        )

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
        self.setGeometry(100, 100, 600, 500)
        self.attesa_risposta = False

        self.setWindowFlags(
            Qt.FramelessWindowHint |  # niente barra superiore
            Qt.WindowStaysOnTopHint   # sempre in primo piano
        )

        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: Arial; font-size: 13px; }
            QTextEdit { background-color: #2e2e2e; color: white; border: 1px solid #444; border-radius: 10px; padding: 8px; }
            QPushButton { background-color: #444; color: white; border: none; }
            QPushButton:hover { background-color: #666; }
            QScrollBar:vertical { background: transparent; width: 8px; }
            QScrollBar::handle:vertical { background: white; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollArea { border: none; }
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
        self.add_image_button.setIcon(QIcon(ICON_PATH("load.svg")))
        self.add_image_button.setIconSize(QSize(24, 24))
        self.add_image_button.setFixedSize(40, 40)
        self.add_image_button.setStyleSheet("QPushButton { border-radius: 20px; background-color: white; }")
        self.add_image_button.clicked.connect(self.carica_immagine)

        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(ICON_PATH("send.svg")))
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

        self.show()

        # if platform.system() == "Darwin":
        #     self.mac_timer = QTimer()
        #     self.mac_timer.setInterval(200)
        #     self.mac_timer.timeout.connect(self.raise_mac_window)
        #     self.mac_timer.start()

        if platform.system() == "Darwin":
            self.mac_timer = QTimer()
            self.mac_timer.setInterval(200)
            self.mac_timer.timeout.connect(self.raise_mac_window)
            QTimer.singleShot(500, self.mac_timer.start)  # ⬅️ ritarda l'avvio

    def raise_mac_window(self):
        try:
            win_id = int(self.winId())
            if win_id == 0:
                return  # ID non pronto

            raw_obj = pyobjc_id(win_id)
            if not raw_obj:
                return  # ancora non pronto o non valido

            ns_window = objc.objc_object(c_void_p=raw_obj)

            if ns_window is None:
                return  # oggetto non valido

            ns_window.setLevel_(NSPopUpMenuWindowLevel)
            ns_window.orderFrontRegardless()
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

        except Exception as e:
            # Debug silenzioso, commenta questa riga se non ti interessa il log
            # print("[macOS] Errore setLevel (iniziale, innocuo):", e)
            pass

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if platform.system() == "Darwin":
            QTimer.singleShot(50, self.raise_mac_window)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if platform.system() == "Darwin":
            QTimer.singleShot(50, self.raise_mac_window)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

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
            self.delete_button.setIcon(QIcon(ICON_PATH("trash.svg")))
            self.delete_button.setIconSize(QSize(20, 20))
            self.delete_button.setFixedSize(28, 28)
            self.delete_button.setStyleSheet("""
                QPushButton { background-color: #444; color: white; border-radius: 14px; }
                QPushButton:hover { background-color: #c00; }
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

    def closeEvent(self, event):
        event.ignore()  # Blocco chiusura manuale

def lancia_gui():
    global qt_app, chat_window

    if qt_app is None:
        qt_app = QApplication.instance() or QApplication(sys.argv)

    if chat_window is None:
        chat_window = GenAIClient()
        chat_window.show()
        print("[INFO] GenAI UI avviata.")

    QTimer.singleShot(0, qt_app.processEvents)

def avvia_gui_esternamente():
    app = QApplication(sys.argv)
    window = GenAIClient()
    window.show()
    sys.exit(app.exec_())
