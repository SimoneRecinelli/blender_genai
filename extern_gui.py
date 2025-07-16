import sys
import os
import requests
import socket
import threading
import platform
from ctypes import c_void_p

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QFileDialog, QSizePolicy, QDialog,
    QCheckBox, QFrame
)
from PyQt5.QtGui import QIcon, QPixmap, QMovie
from PyQt5.QtCore import QCoreApplication, Qt, QTimer, QSize, QPropertyAnimation, QRect
from PyQt5.QtSvg import QSvgWidget

# PyObjC per macOS (aggiunta al sys.path se necessario)
if platform.system() == "Darwin":
    user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
    if user_site not in sys.path:
        sys.path.append(user_site)
    import objc
    from objc import pyobjc_id
    from AppKit import NSApplication, NSWindow, NSPopUpMenuWindowLevel

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

class ImageViewer(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Immagine Ingrandita")
        self.setWindowState(Qt.WindowFullScreen)
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()
        label = QLabel()
        screen_size = QApplication.primaryScreen().availableGeometry().size()

        pixmap = QPixmap(image_path).scaled(
            screen_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)
        self.show()

    def mousePressEvent(self, event):
        self.close()

class ThemeSwitch(QWidget):
    def __init__(self, on_toggle):
        super().__init__()
        self.setFixedSize(70, 36)
        self.on_toggle = on_toggle
        self.state = False  # dark mode iniziale
        self.setCursor(Qt.PointingHandCursor)

        # === Contenitore grigio fisso ===
        self.track = QFrame(self)
        self.track.setGeometry(0, 0, 70, 36)
        self.track.setStyleSheet("background-color: #ddd; border-radius: 18px;")
        self.track.setAttribute(Qt.WA_StyledBackground, True)

        # === Icone SVG
        self.icon_moon = QSvgWidget(os.path.join(BASE_DIR, "icons/moon.svg"), self.track)
        self.icon_moon.setFixedSize(16, 16)
        self.icon_moon.move(8, 10)

        self.icon_sun = QSvgWidget(os.path.join(BASE_DIR, "icons/sun.svg"), self.track)
        self.icon_sun.setFixedSize(16, 16)
        self.icon_sun.move(46, 10)

        # === Pallina bianca
        self.thumb = QFrame(self)
        self.thumb.setGeometry(2, 2, 32, 32)
        self.thumb.setStyleSheet("background-color: white; border-radius: 16px;")
        self.thumb.setAttribute(Qt.WA_StyledBackground, True)

        # === Animazione
        self.anim = QPropertyAnimation(self.thumb, b"geometry")
        self.anim.setDuration(200)

        # === Attiva toggle al click
        self.track.mousePressEvent = self.toggle_theme
        self.thumb.mousePressEvent = self.toggle_theme

    def toggle_theme(self, event=None):
        self.state = not self.state

        # Pallina destra/sinistra
        new_geom = QRect(36, 2, 32, 32) if self.state else QRect(2, 2, 32, 32)
        self.anim.setEndValue(new_geom)
        self.anim.start()

        # Callback al programma principale
        self.on_toggle(self.state)

class GenAIClient(QWidget):
    def __init__(self):
        super().__init__()

        # === Imposta l'icona della finestra in base al sistema operativo ===
        if platform.system() == "Darwin":
            from AppKit import NSApplication, NSImage
            icon_path = os.path.join(BASE_DIR, "icons", "genai_icon.icns")
            nsimage = NSImage.alloc().initWithContentsOfFile_(icon_path)
            if nsimage:
                NSApplication.sharedApplication().setApplicationIconImage_(nsimage)
        elif platform.system() == "Windows":
            icon_path = os.path.join(BASE_DIR, "icons", "genai_icon.ico")
        else:
            icon_path = os.path.join(BASE_DIR, "icons", "genai_icon.png")

        # Usa QIcon cross-platform
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"[AVVISO] Icona non trovata: {icon_path}")

        self.dark_stylesheet = """
            QWidget { background-color: #1e1e1e; color: white; font-family: Arial; font-size: 13px; }
            QTextEdit { background-color: #2e2e2e; color: white; border: 1px solid #444; border-radius: 10px; padding: 8px; }
            QPushButton { background-color: #444; color: white; border: none; }
            QPushButton:hover { background-color: #666; }
            QScrollBar:vertical { background: transparent; width: 8px; }
            QScrollBar::handle:vertical { background: white; border-radius: 4px; min-height: 20px; }
            QScrollArea { border: none; }
        """

        self.light_stylesheet = """
            QWidget { background-color: #f4f4f4; color: black; font-family: Arial; font-size: 13px; }
            QTextEdit { background-color: #ffffff; color: black; border: 1px solid #ccc; border-radius: 10px; padding: 8px; }
            QPushButton { background-color: #ddd; color: black; border: none; }
            QPushButton:hover { background-color: #bbb; }
            QScrollBar:vertical { background: transparent; width: 8px; }
            QScrollBar::handle:vertical { background: #999; border-radius: 4px; min-height: 20px; }
            QScrollArea { border: none; }
        """

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("GenAI Assistant Chat")
        threading.Thread(target=self.listen_for_front_request, daemon=True).start()
        self.setGeometry(100, 100, 600, 500)
        self.attesa_risposta = False
        self._mouse_pos = None

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
        self.add_image_button.setCursor(Qt.PointingHandCursor)
        self.add_image_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #ddd;
            }
        """)

        self.add_image_button.clicked.connect(self.carica_immagine)

        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(ICON_SEND))
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setFixedSize(40, 40)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #ddd;
            }
        """)
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

        # === Switch moderno centrato ===
        self.theme_switch = ThemeSwitch(self.toggle_tema)
        switch_row = QHBoxLayout()
        switch_row.addStretch()
        switch_row.addWidget(self.theme_switch)
        switch_row.addStretch()
        self.main_layout.addLayout(switch_row)

        self.setStyleSheet(self.dark_stylesheet)
        self.setLayout(self.main_layout)

        self.image_path = None
        self.image_preview_label = None
        self.delete_button = None
        self.image_container = None
        self.loading_label = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_response)

        self.show()
        self.raise_mac_window()

    def toggle_tema(self, enabled: bool):
        # 1. Disattiva aggiornamenti
        self.setUpdatesEnabled(False)

        # 2. Salva geometria attuale
        geom = self.geometry()

        # 3. Applica stylesheet
        self.setStyleSheet(self.light_stylesheet if enabled else self.dark_stylesheet)

        # 4. Ripristina geometria
        self.setGeometry(geom)

        # 5. Re-enable updates and repaint
        self.setUpdatesEnabled(True)
        self.repaint()
        self.update()

    def mostra_immagine_intera(self, event):
        if self.image_path and os.path.exists(self.image_path):
            # 🔽 Rimuove temporaneamente "always on top"
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.show()

            viewer = ImageViewer(self.image_path)
            viewer.exec_()

            # 🔼 Ripristina always on top dopo la chiusura
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
            self.raise_mac_window()

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

    def raise_mac_window(self):
        try:
            win_id = int(self.winId())
            if win_id == 0:
                return
            raw_obj = pyobjc_id(win_id)
            if not raw_obj:
                return
            ns_window = objc.objc_object(c_void_p=raw_obj)
            if ns_window is None:
                return
            ns_window.setLevel_(NSPopUpMenuWindowLevel)
            ns_window.orderFrontRegardless()
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
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
        if event.buttons() == Qt.LeftButton and self._mouse_pos is not None:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def closeEvent(self, event):
        from utils import reset_chat_history
        reset_chat_history()
        event.accept()

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
        label.setStyleSheet("font-size: 14px;")
        label.setFixedWidth(390)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        label.setAlignment(Qt.AlignRight if sender == 'user' else Qt.AlignLeft)

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
        layout.addWidget(wrapper_widget)
        container.setLayout(layout)
        self.chat_layout.addWidget(container)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def invia_domanda(self):
        domanda = self.textbox.toPlainText().strip()

        # Blocco se non c'è né testo né immagine
        if not domanda and not self.image_path:
            self.add_message("Inserisci un messaggio o carica un'immagine.", 'bot')
            return

        self.attesa_risposta = True
        self.send_button.setEnabled(False)

        # Mostra il messaggio utente con immagine e/o testo
        if domanda:
            self.add_message(domanda, 'user', image_path=self.image_path)
        else:
            self.add_message("", 'user', image_path=self.image_path)

        self.textbox.clear()
        self.rimuovi_immagine()

        # Spinner di caricamento
        self.loading_label = QLabel()
        movie = QMovie(LOADING_GIF)
        self.loading_label.setMovie(movie)
        movie.start()
        self.chat_layout.addWidget(self.loading_label)

        try:
            # Non forzare una domanda se manca il testo
            payload = {"question": domanda}
            if self.image_path:
                payload["image_path"] = self.image_path

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
        self.hide()  # Nasconde la finestra della chat prima dello screenshot
        QApplication.processEvents()
        QTimer.singleShot(500, self._esegui_screenshot)

    def _esegui_screenshot(self):
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
                subprocess.run(["osascript", "-e", 'tell application "Blender" to activate'])
            except Exception as e:
                self.add_message(f"Errore attivazione Blender: {str(e)}", "bot")

        def get_blender_window_bounds():
            options = kCGWindowListOptionOnScreenOnly
            windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            for window in windowList:
                if "Blender" in window.get("kCGWindowOwnerName", ""):
                    bounds = window.get("kCGWindowBounds", {})
                    return (
                        int(bounds.get("X", 0)),
                        int(bounds.get("Y", 0)),
                        int(bounds.get("Width", 0)),
                        int(bounds.get("Height", 0))
                    )
            return None

        try:
            bring_blender_to_front()
            QApplication.processEvents()
            QApplication.instance().thread().msleep(300)

            bounds = get_blender_window_bounds()
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(0)

            if bounds:
                dpr = screen.devicePixelRatio()
                screen_height = screen.size().height() * dpr

                x, y, w, h = bounds
                x = int(x * dpr)
                y = int((screen_height - y - h) * dpr)
                w = int(w * dpr)
                h = int(h * dpr)

                cropped = screenshot.copy(x, y, w, h)
            else:
                self.add_message("Finestra di Blender non trovata, screenshot dell'intero schermo.", "bot")
                cropped = screenshot

            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"/tmp/blender_screenshot_{now}.png"
            cropped.save(path)
            self.image_path = path

            # Pulisce preview precedente
            for i in reversed(range(self.preview_layout.count())):
                widget = self.preview_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Anteprima immagine
            self.image_preview_label = QLabel()
            pixmap = QPixmap(path).scaledToWidth(100, Qt.SmoothTransformation)
            self.image_preview_label.setPixmap(pixmap)
            self.image_preview_label.setFixedSize(pixmap.size())
            self.image_preview_label.setCursor(Qt.PointingHandCursor)
            self.image_preview_label.mousePressEvent = self.mostra_immagine_intera

            # Bottone elimina
            self.delete_button = QPushButton()
            self.delete_button.setIcon(QIcon(ICON_TRASH))
            self.delete_button.setIconSize(QSize(20, 20))
            self.delete_button.setFixedSize(28, 28)
            self.delete_button.setCursor(Qt.PointingHandCursor)
            self.delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #ddd;
                    color: white;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #c00;
                }
            """)
            self.delete_button.clicked.connect(self.rimuovi_immagine)

            # Layout con immagine a sinistra e bottone a destra
            container = QWidget()
            outer_layout = QHBoxLayout()
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)

            img_container = QWidget()
            img_layout = QHBoxLayout()
            img_layout.setContentsMargins(10, 0, 0, 0)
            img_layout.setSpacing(0)
            img_layout.addWidget(self.image_preview_label)
            img_container.setLayout(img_layout)

            btn_container = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 10, 0)
            btn_layout.addStretch()
            btn_layout.addWidget(self.delete_button)
            btn_container.setLayout(btn_layout)

            outer_layout.addWidget(img_container)
            outer_layout.addStretch()
            outer_layout.addWidget(btn_container)
            container.setLayout(outer_layout)

            self.image_container = container
            self.preview_layout.addWidget(container)


        except Exception as e:
            self.add_message(f"Errore durante la cattura: {str(e)}", "bot")
        finally:
            self.show()
            self.raise_mac_window()

    def rimuovi_immagine(self):
        self.image_path = None
        if self.image_container:
            self.image_container.deleteLater()
        self.image_container = None
        self.image_preview_label = None
        self.delete_button = None

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication.instance() or QApplication(sys.argv)
    window = GenAIClient()
    app.exec_()
