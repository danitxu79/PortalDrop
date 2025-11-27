import sys
import socket
import io
import os
import qrcode
import http.server
import socketserver
import urllib.parse
import re
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                               QPushButton, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon # <--- Importamos QIcon

# --- LÓGICA DE RED (BACKEND) ---
# (Esta parte no cambia, es igual a la V2.1)

class NetworkUtils:
    @staticmethod
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    @staticmethod
    def generate_qr_pixmap(data: str) -> QPixmap:
        qr_image = qrcode.make(data, border=2)
        buffer = io.BytesIO()
        qr_image.save(buffer, format="PNG")
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        return QPixmap.fromImage(qimage)

class SendServerThread(QThread):
    def __init__(self, file_path, port):
        super().__init__()
        self.file_path = file_path
        self.port = port
        self.httpd = None

    def run(self):
        directory = self.file_path.parent
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(directory), **kwargs)
            def log_message(self, format, *args): pass

        try:
            socketserver.TCPServer.allow_reuse_address = True
            self.httpd = socketserver.TCPServer(("", self.port), Handler)
            self.httpd.serve_forever()
        except Exception as e:
            print(f"Error SendServer: {e}")

    def stop_server(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.wait()

class ReceiveServerThread(QThread):
    file_received = Signal(str)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.httpd = None
        self.upload_dir = Path.home() / "Downloads"

    def run(self):
        padre = self
        class UploadHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args): pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <html>
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: sans-serif; background: #2b2b2b; color: white; text-align: center; padding: 20px; }
                        .box { border: 2px dashed #aaa; padding: 40px; border-radius: 10px; margin-top: 50px; }
                        input[type="file"] { display: none; }
                        .btn { background: #d32f2f; color: white; padding: 15px 30px; border-radius: 5px; font-size: 18px; display: inline-block; cursor: pointer; }
                        h2 { margin-bottom: 30px; }
                    </style>
                </head>
                <body>
                    <h2>PortalDrop Inverso</h2>
                    <div class="box">
                        <form method="POST" enctype="multipart/form-data">
                            <label class="btn">
                                📂 Seleccionar Archivo
                                <input type="file" name="file" onchange="this.form.submit()">
                            </label>
                        </form>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))

            def do_POST(self):
                try:
                    content_type = self.headers.get('Content-Type', '')
                    if 'multipart/form-data' not in content_type: return
                    boundary = content_type.split("boundary=")[1].encode()
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length)
                    parts = body.split(b'--' + boundary)

                    for part in parts:
                        if b'Content-Disposition' in part and b'filename="' in part:
                            headers_raw, content = part.split(b'\r\n\r\n', 1)
                            content = content.rstrip(b'\r\n')
                            headers_str = headers_raw.decode(errors='ignore')
                            match = re.search(r'filename="(.+?)"', headers_str)
                            if match:
                                filename = Path(match.group(1)).name
                            else:
                                import time
                                filename = f"PortalDrop_{int(time.time())}.bin"

                            filepath = padre.upload_dir / filename
                            with open(filepath, 'wb') as f: f.write(content)
                            padre.file_received.emit(str(filepath))

                            self.send_response(200)
                            self.send_header("Content-type", "text/html")
                            self.end_headers()
                            self.wfile.write(b"<h1 style='color:green; text-align:center;'>Recibido OK!</h1>")
                            return
                except Exception as e: print(f"Error Upload: {e}")

        try:
            socketserver.TCPServer.allow_reuse_address = True
            self.httpd = socketserver.TCPServer(("", self.port), UploadHandler)
            self.httpd.serve_forever()
        except Exception as e: print(f"Error ReceiveServer: {e}")

    def stop_server(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.wait()


# --- INTERFAZ GRÁFICA (FRONTEND) ---

class PortalDropWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PortalDrop")
        self.resize(400, 550)
        self.setAcceptDrops(True)
        self.port = 8000
        self.active_thread = None

        # --- CARGAR ICONO ---
        #PyInstaller descomprime los datos en una carpeta temporal _MEIPASS
        if getattr(sys, 'frozen', False):
            # Estamos corriendo en modo compilado (PyInstaller)
            base_path = Path(sys._MEIPASS)
        else:
            # Estamos corriendo como script normal .py
            base_path = Path(__file__).parent

        icon_path = base_path / "portaldrop-512.png"

        if icon_path.exists():
            self.app_icon = QIcon(str(icon_path))
            self.setWindowIcon(self.app_icon) # Icono de la ventana/barra tareas
        else:
            self.app_icon = None
            print("Aviso: No se encontró portaldrop-512.png")

        # Layout Setup
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # --- MENU PRINCIPAL ---
        self.page_menu = QWidget()
        layout_menu = QVBoxLayout()
        self.page_menu.setLayout(layout_menu)

        # LOGO O TEXTO
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Si tenemos icono, lo mostramos en grande. Si no, texto.
        if self.app_icon:
            pixmap = self.app_icon.pixmap(128, 128) # Tamaño 128x128
            lbl_logo.setPixmap(pixmap)
        else:
            lbl_logo.setText("PortalDrop")
            lbl_logo.setStyleSheet("font-size: 30px; font-weight: bold; color: white;")

        lbl_title = QLabel("PortalDrop") # Título debajo del logo
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-top: 10px;")

        lbl_inst = QLabel("Arrastra un archivo para ENVIAR\n- O -")
        lbl_inst.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_inst.setStyleSheet("color: #aaa; margin: 20px;")

        self.btn_receive = QPushButton("📡 Recibir del Móvil")
        self.btn_receive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_receive.clicked.connect(self.start_receive_mode)

        layout_menu.addStretch()
        layout_menu.addWidget(lbl_logo)
        layout_menu.addWidget(lbl_title) # Añadido el título explícito
        layout_menu.addWidget(lbl_inst)
        layout_menu.addWidget(self.btn_receive)
        layout_menu.addStretch()

        # --- PANTALLA ACTIVA ---
        self.page_active = QWidget()
        layout_active = QVBoxLayout()
        self.page_active.setLayout(layout_active)

        self.lbl_status = QLabel("Esperando...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")

        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr.setStyleSheet("border: 10px solid white; border-radius: 4px; background-color: white;")

        self.lbl_url = QLabel("http://...")
        self.lbl_url.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_url.setStyleSheet("color: #888; margin-bottom: 20px;")

        self.btn_stop = QPushButton("Detener")
        self.btn_stop.clicked.connect(self.reset_state)

        layout_active.addWidget(self.lbl_status)
        layout_active.addStretch()
        layout_active.addWidget(self.lbl_qr)
        layout_active.addWidget(self.lbl_url)
        layout_active.addStretch()
        layout_active.addWidget(self.btn_stop)

        self.stack.addWidget(self.page_menu)
        self.stack.addWidget(self.page_active)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: sans-serif; }
            QPushButton { background-color: #2196F3; color: white; border: none; padding: 15px; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton#btn_stop { background-color: #d32f2f; }
        """)
        self.btn_stop.setObjectName("btn_stop")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.start_send_mode(Path(urls[0].toLocalFile()))

    def start_send_mode(self, file_path):
        self.stop_any_server()
        self.active_thread = SendServerThread(file_path, self.port)
        self.active_thread.start()
        self.show_qr_page(f"Sirviendo: {file_path.name}", f"/{urllib.parse.quote(file_path.name)}")

    def start_receive_mode(self):
        self.stop_any_server()
        self.active_thread = ReceiveServerThread(self.port)
        self.active_thread.file_received.connect(self.on_file_received)
        self.active_thread.start()
        self.show_qr_page("Escanea para SUBIR archivo", "")

    def show_qr_page(self, status_text, url_suffix):
        local_ip = NetworkUtils.get_local_ip()
        url = f"http://{local_ip}:{self.port}{url_suffix}"
        self.lbl_status.setText(status_text)
        self.lbl_url.setText(url)
        self.lbl_qr.setPixmap(NetworkUtils.generate_qr_pixmap(url).scaled(250, 250))
        self.stack.setCurrentIndex(1)

    def on_file_received(self, filepath):
        QMessageBox.information(self, "¡Archivo Recibido!", f"Guardado en:\n{filepath}")
        self.reset_state()

    def stop_any_server(self):
        if self.active_thread:
            self.active_thread.stop_server()
            self.active_thread = None

    def reset_state(self):
        self.stop_any_server()
        self.stack.setCurrentIndex(0)

    def closeEvent(self, event):
        self.stop_any_server()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # INTENTO EXTRA PARA LINUX (GNOME/UBUNTU)
    # A veces el icono no sale en el dock si no le dices a Qt que es una "App de escritorio"
    # Esto asigna un ID a la aplicación.
    if sys.platform == 'linux':
        try:
            import ctypes
            myappid = 'portaldrop.linux.gui.v2'
            ctypes.cdll.LoadLibrary('libgtk-3.so.0')
        except:
            pass

    window = PortalDropWindow()
    window.show()
    sys.exit(app.exec())
