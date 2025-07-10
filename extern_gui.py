import sys
print("INTERPRETER IN USO DALLA GUI:", sys.executable)
import os
import requests
import socket
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QFileDialog, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer, QSize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_SEND = os.path.join(BASE_DIR, "icons", "send.svg")
ICON_LOAD = os.path.join(BASE_DIR, "icons", "load.svg")
ICON_TRASH = os.path.join(BASE_DIR, "icons", "trash.svg")
LOADING_GIF = os.path.join(BASE_DIR, "icons", "loading.gif")

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
        threading.Thread(target=self.listen_for_front_request, daemon=True).start()
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
        self.add_image_button.setIcon(QIcon(ICON_LOAD))
        self.add_image_button.setIconSize(QSize(24, 24))
        self.add_image_button.setFixedSize(40, 40)
        self.add_image_button.setStyleSheet("QPushButton { border-radius: 20px; background-color: white; }")
        self.add_image_button.clicked.connect(self.carica_immagine)

        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(ICON_SEND))
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

    def listen_for_front_request(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("localhost", 5055))
            s.listen(1)
            while True:
                conn, _ = s.accept()
                data = conn.recv(1024)
                if b"bring-to-front" in data:
                    self.showNormal()
                    self.raise_()
                    self.activateWindow()
                conn.close()
        except OSError:
            print("[DEBUG] Porta già in uso — GUI probabilmente già attiva")

    '''
    def add_message(self, text, sender='user', image_path=None):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(image_path).scaledToWidth(250, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignLeft if sender == 'bot' else Qt.AlignRight)
            layout.addWidget(image_label)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet("font-size: 14px; padding: 6px;")
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        label.setMaximumWidth(int(self.width() * 0.7))


        #label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet("font-size: 14px;")
        #label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)

        if sender == 'user':
            wrapper.addStretch()
            wrapper.addWidget(label, 0, Qt.AlignRight)
        else:
            wrapper.addWidget(label, 0, Qt.AlignLeft)
            wrapper.addStretch()

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper)

        layout.addWidget(wrapper_widget)
        container.setLayout(layout)

        self.chat_layout.addWidget(container)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))
    '''

    def add_message(self, text, sender='user', image_path=None):
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 5, 10, 5)
        container_layout.setSpacing(5)

        # Se presente, aggiungi immagine
        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(image_path).scaledToWidth(250, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignLeft if sender == 'bot' else Qt.AlignRight)
            image_label.setContentsMargins(0, 0, 0, 10)
            container_layout.addWidget(image_label)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet("font-size: 14px;")
        label.setFixedWidth(390)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        label.setAlignment(Qt.AlignRight if sender == 'user' else Qt.AlignLeft)


        label.setFixedWidth(390)  # Larghezza fissa scelta in base alla tua finestra
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        # Contenitore orizzontale per allineare a destra/sinistra
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        if sender == 'user':
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(label, 0, Qt.AlignRight)
        else:
            wrapper_layout.addWidget(label, 0, Qt.AlignLeft)
            wrapper_layout.addStretch()

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper_layout)

        container_layout.addWidget(wrapper_widget)
        container.setLayout(container_layout)

        self.chat_layout.addWidget(container)

        # Scroll automatico alla fine
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))


    def invia_domanda(self):
        domanda = self.textbox.toPlainText().strip()
        if not domanda or self.attesa_risposta:
            return

        self.attesa_risposta = True
        self.send_button.setEnabled(False)
        self.add_message(domanda, 'user', image_path=self.image_path)
        self.textbox.clear()
        self.rimuovi_immagine()

        self.loading_label = QLabel()
        movie = QMovie(LOADING_GIF)
        self.loading_label.setMovie(movie)
        movie.start()
        self.chat_layout.addWidget(self.loading_label)

        try:
            payload = {"question": domanda}
            if self.image_path:
                payload["image_path"] = self.image_path
                print(f"[DEBUG] self.image_path = {self.image_path}")
                print(f"[DEBUG] os.path.exists(self.image_path): {os.path.exists(self.image_path)}")


            print(f"[DEBUG] Domanda: {domanda}")
            if "image_path" in payload:
                print(f"[DEBUG] Inviando immagine: {payload['image_path']}")
            else:
                print("[DEBUG] Nessuna immagine inclusa")

            r = requests.post("http://127.0.0.1:5000/ask", json=payload)
            if r.status_code == 200:
                self.timer.start(2000)
            else:
                self.loading_label.hide()
                self.add_message("Errore nella richiesta a Blender.", 'bot')
                self.send_button.setEnabled(True)
                self.attesa_risposta = False
        except Exception as e:
            self.loading_label.hide()
            self.add_message(f"Errore: {str(e)}", 'bot')
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
            self.add_message(f"Errore: {str(e)}", 'bot')

    def carica_immagine(self):
        import datetime
        import subprocess
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        def bring_blender_to_front():
            try:
                script = '''
                tell application "Blender"
                    activate
                end tell
                '''
                subprocess.run(["osascript", "-e", script])
            except Exception as e:
                self.add_message(f"Errore attivazione Blender: {str(e)}", "bot")

        def get_blender_window_bounds():
            options = kCGWindowListOptionOnScreenOnly
            windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            for window in windowList:
                if "Blender" in window.get("kCGWindowOwnerName", ""):
                    bounds = window.get("kCGWindowBounds", {})
                    x = int(bounds.get("X", 0))
                    y = int(bounds.get("Y", 0))
                    w = int(bounds.get("Width", 0))
                    h = int(bounds.get("Height", 0))
                    screen_height = QApplication.primaryScreen().size().height()
                    y = screen_height - y - h  # conversione da coordinate macOS a Qt
                    return (x, y, w, h)
            return None

        try:
            bring_blender_to_front()
            QApplication.processEvents()
            self.repaint()
            QApplication.instance().thread().msleep(500)

            bounds = get_blender_window_bounds()
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(0)

            if bounds:
                screen = QApplication.primaryScreen()
                device_pixel_ratio = screen.devicePixelRatio()

                x, y, w, h = bounds
                x *= device_pixel_ratio
                y *= device_pixel_ratio
                w *= device_pixel_ratio
                h *= device_pixel_ratio

                cropped = screenshot.copy(int(x), int(y), int(w), int(h))
            else:
                self.add_message("Finestra di Blender non trovata, uso schermo intero", "bot")
                cropped = screenshot

            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"/tmp/blender_screenshot_{now}.png"
            cropped.save(path)
            self.image_path = path

            # Pulisci preview precedente
            for i in reversed(range(self.preview_layout.count())):
                widget = self.preview_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Anteprima + bottone elimina
            self.image_preview_label = QLabel()
            pixmap = QPixmap(path).scaledToWidth(100, Qt.SmoothTransformation)
            self.image_preview_label.setPixmap(pixmap)

            self.delete_button = QPushButton()
            self.delete_button.setIcon(QIcon(ICON_TRASH))
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

        except Exception as e:
            self.add_message(f"Errore durante la cattura della finestra: {str(e)}", "bot")


    def rimuovi_immagine(self):
        self.image_path = None
        if self.image_container:
            self.image_container.deleteLater()
        self.image_container = None
        self.image_preview_label = None
        self.delete_button = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GenAIClient()
    win.show()
    sys.exit(app.exec_())
