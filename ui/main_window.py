import sys
import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QStackedWidget, QMessageBox, QTabWidget,
    QProgressBar,
)

from PyQt6.QtGui import (
    QIcon, QFont, QPixmap
)

from PyQt6.QtCore import (
    Qt, QTimer
)

from config.settings import API_ID, API_HASH, SESSION_NAME
from telegram.async_worker import AsyncWorker
from ui.widgets import ChatListWidget
from ui.dialogs import DateRangeDialog, MediaSelectionDialog, ChatPreviewDialog
from ui.threads_results_view import ThreadsAnalysisResults

# Nueva clase para la ventana de resultados de análisis de sentimientos
class SentimentAnalysisDialog(QDialog):
    def __init__(self, summary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Análisis de Sentimientos")
        self.setGeometry(400, 200, 600, 500)
        self.setModal(True)  # Bloquea la ventana principal hasta cerrar
        
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("<h3>Análisis de Sentimientos</h3>")
        layout.addWidget(title)
        
        # Scroll area para contenido largo
        from PyQt6.QtWidgets import QScrollArea, QWidget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Resumen general
        general_text = f"""
        <h4>Resumen General</h4>
        <p><b>Total de Mensajes Analizados:</b> {summary.get('total_messages', 0)}</p>
        <p><b>Puntuación Promedio:</b> {summary.get('average_score', 0.0)}</p>
        <p><b>Sentimiento Más Común:</b> {summary.get('most_common_sentiment', 'N/A')}</p>
        <h5>Distribución General:</h5>
        <ul>
        """
        for label, count in summary.get('distribution', {}).items():
            general_text += f"<li>{label.capitalize()}: {count}</li>"
        general_text += "</ul><h5>Porcentajes Generales:</h5><ul>"
        for label, perc in summary.get('percentages', {}).items():
            general_text += f"<li>{label.capitalize()}: {perc}%</li>"
        general_text += "</ul>"
        
        general_label = QLabel(general_text)
        general_label.setWordWrap(True)
        general_label.setStyleSheet("font-size: 12px; padding: 10px;")
        content_layout.addWidget(general_label)
        
        # Análisis por usuario
        user_sentiments = summary.get('user_sentiments', {})
        if user_sentiments:
            user_title = QLabel("<h4>Análisis por Participante</h4>")
            content_layout.addWidget(user_title)
            
            for user, data in user_sentiments.items():
                user_text = f"""
                <p><b>Usuario:</b> {user}</p>
                <p><b>Mensajes:</b> {data['total_messages']}</p>
                <p><b>Puntuación Promedio:</b> {data['average_score']}</p>
                <p><b>Sentimiento Más Común:</b> {data['most_common_sentiment']}</p>
                <p><b>Distribución:</b> {data['distribution']}</p>
                <p><b>Porcentajes:</b> {data['percentages']}</p>
                <hr>
                """
                user_label = QLabel(user_text)
                user_label.setWordWrap(True)
                user_label.setStyleSheet("font-size: 11px; padding: 5px; background-color: #f9f9f9;")
                content_layout.addWidget(user_label)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Botón para cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class TelegramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asistente de Telegram")
        self.setGeometry(300, 150, 420, 620)
        self.setWindowIcon(QIcon("telegram_icon.png"))

        if API_ID == 0 or not API_HASH:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudieron cargar API_ID y API_HASH.\nPor favor, configura el archivo .env correctamente.",
            )
            sys.exit(1)

        self.client = None
        self.has_active_session = False
        self.current_user_phone = None

        self.worker = AsyncWorker(None)

        self.setup_ui()
        self.setup_worker_signals()

        QTimer.singleShot(100, self.check_existing_session)

    def create_worker(self):
        worker = AsyncWorker(None)
        worker.success.connect(self.on_success)
        worker.error.connect(self.on_error)
        worker.chats_loaded.connect(self.on_chats_loaded)
        worker.code_sent.connect(self.on_code_sent)
        worker.download_progress.connect(self.on_download_progress)
        worker.download_completed.connect(self.on_download_completed)
        worker.sentiment_analysis_completed.connect(self.on_sentiment_analysis_completed)  # Nueva conexión
        return worker

    async def get_client(self):
        return await self.worker.get_client()

    def setup_ui(self):
        self.stack = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.setup_phone_screen()
        self.setup_code_screen()
        self.setup_chat_screen()

    def setup_phone_screen(self):
        self.phone_screen = QWidget()
        phone_layout = QVBoxLayout()
        phone_layout.setContentsMargins(20, 20, 20, 20)
        phone_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        icon_label = QLabel()
        try:
            pix = QPixmap("telegram_icon.png")
            if not pix.isNull():
                icon_label.setPixmap(
                    pix.scaled(
                        48, 48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        except Exception:
            pass
        header_layout.addWidget(icon_label)

        title = QLabel(
            "<h2 style='margin:0; color:#2C6E91;'>Bienvenido a nuestro asistente de Telegram</h2>"
        )
        title.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addStretch()
        phone_layout.addLayout(header_layout)

        desc = QLabel(
            "<p style='font-size:13px; color:#444; margin-top:6px;'>"
            "Esta aplicación te ayuda a exportar y analizar conversaciones de Telegram. "
            "Primero debes iniciar sesión: requerimos tu número de teléfono para enviar "
            "el código de verificación a tu cuenta de Telegram. Si tienes verificación en dos pasos, " 
            "también requerimos tu contraseña. Si deseas mantener tu sesión "
            "activa, puedes quitar la aplicación sin más y podrás entrar más "
            "rápido la próxima vez."
            "</p>"
        )
        desc.setWordWrap(True)
        phone_layout.addWidget(desc)

        phone_layout.addWidget(QLabel("<b>Número de teléfono:</b>"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+34 600 000 000")
        self.phone_input.setFont(QFont("Arial", 12))
        self.phone_input.setFixedHeight(36)
        self.phone_input.setClearButtonEnabled(True)
        self.phone_input.setToolTip("Introduce tu número en formato internacional (ej: +34 600 000 000)")
        phone_layout.addWidget(self.phone_input)

        example_label = QLabel("<small style='color:#666;'>Ejemplo de formato: +34 600 000 000</small>")
        phone_layout.addWidget(example_label)

        phone_layout.addWidget(QLabel("<b>Contraseña (opcional):</b>"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña para verificación en dos pasos")
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(36)
        self.password_input.setClearButtonEnabled(True)
        self.password_input.setToolTip("Si tu cuenta tiene verificación en dos pasos, introdúcelo aquí")
        phone_layout.addWidget(self.password_input)

        pass_help = QLabel(
            "<small style='color:#666;'>Si tienes verificación en dos pasos, es necesario que pongas tu contraseña aquí.</small>"
        )
        phone_layout.addWidget(pass_help)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.restore_btn = QPushButton("Volver a sesión anterior")
        self.restore_btn.setFixedHeight(38)
        self.restore_btn.setVisible(False)
        self.restore_btn.setStyleSheet(
            "QPushButton { background-color:#4a8e6e; color:white; padding:8px; border-radius:8px; font-size:13px; }"
            "QPushButton:hover { background-color:#5fbf8b; }"
        )
        self.restore_btn.clicked.connect(self.restore_previous_session)
        btn_row.addWidget(self.restore_btn)

        btn_row.addSpacing(8)

        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setStyleSheet(
            "QPushButton { background-color:#2C6E91; color:white; padding:10px; border-radius:8px; font-size:14px; }"
            "QPushButton:hover { background-color:#3A88B1; }"
        )
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self.start_login)
        btn_row.addWidget(self.login_btn)

        btn_row.addStretch()
        phone_layout.addLayout(btn_row)

        phone_layout.addStretch()

        self.phone_screen.setLayout(phone_layout)
        self.stack.addWidget(self.phone_screen)

    def check_existing_session(self):
        try:
            session_file = f"{SESSION_NAME}.session"
            if os.path.exists(session_file):
                self.restore_btn.setVisible(True)
                try:
                    self.statusBar().showMessage(
                        "Sesión anterior detectada. Pulsa 'Volver a sesión anterior' para restaurarla.",
                        8000,
                    )
                except Exception:
                    pass
                return True
            else:
                self.restore_btn.setVisible(False)
                return False
        except Exception as e:
            print(f"Error en check_existing_session (UI): {e}")
            return False

    def restore_previous_session(self):
        try:
            self.restore_btn.setEnabled(False)
            self.login_btn.setEnabled(False)
            self.restore_btn.setText("Restaurando...")
        except Exception:
            pass

        if getattr(self, "worker", None) and self.worker.isRunning():
            QMessageBox.information(
                self, "Espera", "Hay una operación en curso. Espera a que termine."
            )
            try:
                self.restore_btn.setEnabled(True)
                self.restore_btn.setText("Volver a sesión anterior")
                self.login_btn.setEnabled(True)
            except Exception:
                pass
            return

        self.worker = self.create_worker()
        self.worker.set_task("verify_session", phone=None, password=None)

        try:
            self.worker.finished.disconnect()
        except Exception:
            pass
        self.worker.finished.connect(lambda: self._after_restore_attempt())
        self.worker.start()

    def _after_restore_attempt(self):
        try:
            self.restore_btn.setEnabled(True)
            self.restore_btn.setText("Volver a sesión anterior")
            self.login_btn.setEnabled(True)
        except Exception:
            pass

    def setup_code_screen(self):
        self.code_screen = QWidget()
        code_layout = QVBoxLayout()
        code_layout.setContentsMargins(20, 20, 20, 20)
        code_layout.setSpacing(10)

        title_label = QLabel("<h2 style='color:#2C6E91; margin:0;'>Verificación</h2>")
        code_layout.addWidget(title_label)

        instructions = QLabel(
            "<div style='color:#444;'>Se ha enviado un código de verificación a tu cuenta de Telegram. "
            "Introduce el código a continuación.</div>"
        )
        instructions.setWordWrap(True)
        code_layout.addWidget(instructions)

        code_layout.addWidget(QLabel("<b>Código de verificación:</b>"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Ej: 12345")
        self.code_input.setFont(QFont("Arial", 13))
        self.code_input.setMaxLength(10)
        self.code_input.setFixedHeight(40)
        self.code_input.setClearButtonEnabled(True)
        code_layout.addWidget(self.code_input)

        self.password_label = QLabel("<b>Pase seguro (2FA) — opcional:</b>")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Pase seguro (si aplica)")
        self.password_input.setFont(QFont("Arial", 13))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_label.setVisible(False)
        self.password_input.setVisible(False)
        code_layout.addWidget(self.password_label)
        code_layout.addWidget(self.password_input)
        # ==================== ui/main_window.py (continuación) ====================
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.verify_btn = QPushButton("Verificar Código")
        self.verify_btn.setFixedHeight(40)
        self.verify_btn.setStyleSheet(
            "QPushButton { background-color:#2C6E91; color:white; padding:8px; border-radius:8px; font-size:14px; }"
            "QPushButton:hover { background-color:#3A88B1; }"
        )
        self.verify_btn.clicked.connect(self.verify_code)
        btn_row.addWidget(self.verify_btn)

        self.resend_btn = QPushButton("Reenviar código")
        self.resend_btn.setFixedHeight(36)
        self.resend_btn.setStyleSheet(
            "QPushButton { background-color:#6c757d; color:white; padding:6px; border-radius:6px; }"
            "QPushButton:hover { background-color:#5a6268; }"
        )
        self.resend_btn.clicked.connect(self.resend_code)
        btn_row.addWidget(self.resend_btn)

        btn_row.addStretch()
        code_layout.addLayout(btn_row)

        code_layout.addStretch()
        self.code_screen.setLayout(code_layout)
        self.stack.addWidget(self.code_screen)

    def setup_chat_screen(self):
        self.chat_screen = QWidget()
        chat_layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        title_label = QLabel("<h3 style='color:#2C6E91;'>Tus Chats y Grupos</h3>")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        self.logout_btn = QPushButton("🔒 Cerrar Sesión")
        self.logout_btn.setStyleSheet(
            "QPushButton { background-color:#dc3545; color:white; padding:8px 12px; border-radius:6px; font-size:12px; }"
            "QPushButton:hover { background-color:#c82333; }"
            "QPushButton:pressed { background-color:#bd2130; }"
        )
        self.logout_btn.setFixedHeight(35)
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)

        chat_layout.addLayout(top_layout)

        self.chat_tabs = QTabWidget()
        self.chat_widgets = {}

        tab_configs = [
            ("Todos", "todos"),
            ("No Leídos", "no_leídos"),
            ("Personales", "personales"),
            ("Grupos", "grupos"),
        ]

        for tab_name, tab_key in tab_configs:
            chat_widget = ChatListWidget()
            self.chat_widgets[tab_key] = chat_widget
            self.chat_tabs.addTab(chat_widget, tab_name)

        # Nueva pestaña para análisis de sentimientos (REMOVIDA - ahora es una ventana)

        chat_layout.addWidget(self.chat_tabs)

        analysis_label = QLabel("<b>Herramientas de Análisis:</b>")
        chat_layout.addWidget(analysis_label)

        buttons_layout = QHBoxLayout()

        self.total_analysis_btn = QPushButton("📊 Análisis Completo")
        self.total_analysis_btn.setStyleSheet(
            "QPushButton { background-color:#28a745; color:white; padding:10px; border-radius:6px; font-weight:bold; font-size:12px; }"
            "QPushButton:hover { background-color:#218838; }"
            "QPushButton:disabled { background-color:#6c757d; color:#ccc; }"
        )
        self.total_analysis_btn.clicked.connect(lambda: self.start_analysis("total"))

        self.important_info_btn = QPushButton("🔍 Información Clave")
        self.important_info_btn.setStyleSheet(
            "QPushButton { background-color:#17a2b8; color:white; padding:10px; border-radius:6px; font-weight:bold; font-size:12px; }"
            "QPushButton:hover { background-color:#138496; }"
            "QPushButton:disabled { background-color:#6c757d; color:#ccc; }"
        )
        self.important_info_btn.clicked.connect(lambda: self.start_analysis("important"))

        self.conversation_threads_btn = QPushButton("💬 Hilos de Conversación")
        self.conversation_threads_btn.setStyleSheet(
            "QPushButton { background-color:#6f42c1; color:white; padding:10px; border-radius:6px; font-weight:bold; font-size:12px; }"
            "QPushButton:hover { background-color:#5a359a; }"
            "QPushButton:disabled { background-color:#6c757d; color:#ccc; }"
        )
        self.conversation_threads_btn.clicked.connect(lambda: self.start_analysis("threads"))

        buttons_layout.addWidget(self.total_analysis_btn)
        buttons_layout.addWidget(self.important_info_btn)
        buttons_layout.addWidget(self.conversation_threads_btn)

        chat_layout.addLayout(buttons_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #ccc; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #2C6E91; border-radius: 4px; }"
        )
        chat_layout.addWidget(self.progress_bar)

        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(self.user_info_label)

        self.chat_screen.setLayout(chat_layout)
        self.stack.addWidget(self.chat_screen)

    def setup_worker_signals(self):
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.chats_loaded.connect(self.on_chats_loaded)
        self.worker.code_sent.connect(self.on_code_sent)
        self.worker.download_progress.connect(self.on_download_progress)
        self.worker.download_completed.connect(self.on_download_completed)
        self.worker.sentiment_analysis_completed.connect(self.on_sentiment_analysis_completed)  
        self.worker.conversation_threads_completed.connect(self.on_conversation_threads_completed) # Nueva señal

    def start_login(self):
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()

        if not phone:
            QMessageBox.warning(self, "Error", "Introduce un número de teléfono válido")
            return

        self.current_user_phone = phone

        try:
            self.restore_btn.setVisible(False)
        except Exception:
            pass

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Verificando...")

        self.worker = self.create_worker()
        self.worker.set_task("verify_session", phone=phone, password=password)

        try:
            self.worker.finished.disconnect()
        except Exception:
            pass
        self.worker.finished.connect(lambda: self.reset_login_button())
        self.worker.start()

    def reset_login_button(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Iniciar Sesión")

    def verify_code(self):
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Introduce el código")
            return

        phone_to_use = (
            getattr(self, "current_user_phone", None) or self.phone_input.text().strip()
        )
        if not phone_to_use:
            QMessageBox.warning(self, "Error", "No hay número de teléfono registrado")
            return

        try:
            btn = self.verify_btn
            btn.setEnabled(False)
            btn.setText("Verificando...")
        except Exception:
            pass

        if self.worker.isRunning():
            self.worker.wait()

        self.worker.set_task("verify_code", phone=phone_to_use, code=code)

        try:
            self.worker.finished.disconnect()
        except Exception:
            pass

        self.worker.finished.connect(lambda: self.reset_verify_button())
        self.worker.start()

    def reset_verify_button(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Verificar")

    def resend_code(self):
        if not self.current_user_phone:
            QMessageBox.warning(self, "Error", "No hay número de teléfono registrado")
            return

        self.resend_btn.setEnabled(False)
        self.resend_btn.setText("Enviando...")

        self.worker = self.create_worker()
        self.worker.set_task("send_code", phone=self.current_user_phone)

        try:
            self.worker.finished.disconnect()
        except Exception:
            pass

        self.worker.finished.connect(lambda: self.reset_resend_button())
        self.worker.start()

    def reset_resend_button(self):
        self.resend_btn.setEnabled(True)
        self.resend_btn.setText("Reenviar Código")

    def update_user_info(self):
        if self.current_user_phone:
            self.user_info_label.setText(f"Conectado como: {self.current_user_phone}")
        else:
            self.user_info_label.setText("")

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Cerrar Sesión",
            "¿Estás seguro de que quieres cerrar la sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                client = loop.run_until_complete(self.get_client())

                if client and client.is_connected():
                    client.disconnect()

                loop.close()

                self.cleanup_existing_sessions()

                self.has_active_session = False
                self.current_user_phone = None

                self.stack.setCurrentWidget(self.phone_screen)
                self.phone_input.clear()
                self.password_input.clear()

                QMessageBox.information(
                    self, "Sesión Cerrada", "Has cerrado sesión correctamente."
                )

            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo cerrar sesión: {e}")

    def cleanup_existing_sessions(self):
        import os
        session_files = [f"{SESSION_NAME}.session", f"{SESSION_NAME}.session-journal"]

        for session_file in session_files:
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                    print(f"Sesión anterior eliminada: {session_file}")
                except Exception as e:
                    print(f"No se pudo eliminar {session_file}: {e}")

    def on_success(self, message):
        if message == "session_valid":
            QMessageBox.information(
                self,
                "Bienvenido",
                "✅ Sesión recuperada exitosamente. Bienvenido de vuelta!",
            )
            self.show_chat_screen_directly()
        elif message == "session_invalid":
            QMessageBox.warning(
                self,
                "Sesión Inválida",
                "El número no coincide con la sesión activa. Se ha cerrado la sesión anterior.",
            )
            self.stack.setCurrentWidget(self.phone_screen)
        elif "código enviado" in message.lower():
            QMessageBox.information(self, "Código Enviado", message)
            self.stack.setCurrentWidget(self.code_screen)
        elif "autenticación completada" in message.lower():
            adv = ". Por favor espere un poco en lo que cargan sus chats..."
            QMessageBox.information(self, "Éxito", message + adv)
            self.has_active_session = True
            self.show_chat_screen_directly()
        else:
            QMessageBox.information(self, "Éxito", message)

    def on_error(self, error_message):
        if error_message == "password_required":
            self.password_label.setVisible(True)
            self.password_input.setVisible(True)
            QMessageBox.information(
                self,
                "Pase Seguro Requerido",
                "Tu cuenta tiene verificación en dos pasos. Por favor, introduce tu pase seguro.",
            )
        else:
            QMessageBox.critical(self, "Error", error_message)

    def on_code_sent(self):
        self.stack.setCurrentWidget(self.code_screen)

    def on_chats_loaded(self, chats_data):
        try:
            for widget in self.chat_widgets.values():
                if hasattr(widget, "clear"):
                    widget.clear()

            while self.chat_tabs.count() > 4:
                self.chat_tabs.removeTab(4)

            for chat in chats_data.get("all", []):
                self.chat_widgets["todos"].add_chat_item(chat)

            for chat in chats_data.get("unread", []):
                self.chat_widgets["no_leídos"].add_chat_item(chat)

            for chat in chats_data.get("personal", []):
                self.chat_widgets["personales"].add_chat_item(chat)

            for chat in chats_data.get("groups", []):
                self.chat_widgets["grupos"].add_chat_item(chat)

            folders = chats_data.get("folders", {}) or {}
            for fname, flist in folders.items():
                folder_widget = ChatListWidget()
                for chat in flist:
                    folder_widget.add_chat_item(chat)
                self.chat_tabs.addTab(folder_widget, f"{fname} ({len(flist)})")

            try:
                self.stack.setCurrentWidget(self.chat_screen)
            except Exception:
                pass

        except Exception as e:
            print(f"Error en on_chats_loaded: {e}")

    def show_chat_screen_directly(self):
        self.stack.setCurrentWidget(self.chat_screen)
        QTimer.singleShot(100, self.load_chats_delayed)

    def load_chats_delayed(self):
        self.worker = self.create_worker()
        self.worker.set_task("load_chats")
        self.worker.start()

    def preview_chat(self, chat_info):
        try:
            if not hasattr(self, "preview_media_options"):
                self.preview_media_options = {
                    "text": True,
                    "images": False,
                    "audio": False,
                    "documents": False,
                }

            worker = self.create_worker()

            def on_preview(msgs):
                self.show_preview_dialog(chat_info, msgs, worker)

            worker.preview_loaded.connect(on_preview)
            worker.set_task(
                "preview_chat",
                selected_chats=[chat_info],
                media_options=self.preview_media_options,
                preview_offset=0,
            )
            worker.preview_limit = 50
            worker.start()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo iniciar vista previa: {e}")

    def show_preview_dialog(self, chat_info, messages, worker):
        try:
            dlg = ChatPreviewDialog(chat_info, messages, worker_ref=worker, parent=self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la vista previa: {e}")

    def preview_with_options(self, chat_info, media_options):
        try:
            worker = self.create_worker()

            def on_preview(msgs):
                self.show_preview_dialog(chat_info, msgs, worker)

            worker.preview_loaded.connect(on_preview)
            worker.set_task(
                "preview_chat",
                selected_chats=[chat_info],
                media_options=media_options,
                preview_offset=0,
            )
            worker.preview_limit = 200
            worker.start()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo recargar preview: {e}")

    def on_download_progress(self, chat_name, current, total):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Procesando: {chat_name} ({current}/{total})")

    def on_download_completed(self, successful, failed):
        """Manejar la finalización de la descarga de chats"""
        self.progress_bar.setVisible(False)
        
        print(f"📥 Descarga completada - Exitosos: {len(successful)}, Fallidos: {len(failed)}")
        
        # Si es análisis de hilos, mostrar los resultados existentes
        if hasattr(self, 'analysis_type') and self.analysis_type == "threads":
            print("🧵 Es análisis de hilos, mostrando resultados...")
            
            # Cerrar diálogo de progreso si existe
            if hasattr(self, 'threads_progress_dialog') and self.threads_progress_dialog:
                try:
                    self.threads_progress_dialog.close()
                    self.threads_progress_dialog = None
                    print("✅ Diálogo de progreso cerrado")
                except Exception as e:
                    print(f"❌ Error cerrando diálogo: {e}")
            
            # Habilitar botones
            self.set_analysis_buttons_enabled(True)
            
            # Buscar todos los archivos de análisis en threads_analysis_results/
            import glob
            analysis_files = glob.glob("threads_analysis_results/*_analysis.json")
            
            if not analysis_files:
                QMessageBox.warning(
                    self, 
                    "Análisis Completo", 
                    "No se encontraron archivos de análisis. Es posible que el procesamiento aún esté en curso."
                )
                return
            
            print(f"📊 Encontrados {len(analysis_files)} archivos de análisis")
            
            # Construir resultados leyendo los archivos existentes
            results = {
                "archivos_procesados": len(analysis_files),
                "archivos_totales": len(analysis_files),
                "resultados_detallados": {},
                "timestamp": datetime.now().isoformat()
            }
            
            for analysis_file in analysis_files:
                try:
                    # Obtener el nombre base del archivo (sin _analysis.json)
                    base_name = os.path.basename(analysis_file).replace('_analysis.json', '')
                    print(f"📖 Leyendo análisis: {base_name}")
                    
                    # Cargar archivo de análisis
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                    
                    # Cargar archivo de hilos para contar hilos
                    threads_file = analysis_file.replace('_analysis.json', '_threads.json')
                    threads_count = 0
                    if os.path.exists(threads_file):
                        with open(threads_file, 'r', encoding='utf-8') as f:
                            threads_data = json.load(f)
                            threads_count = len(threads_data.get('threads', {}))
                    
                    # Cargar archivo de grafo para obtener metadata
                    graph_file = analysis_file.replace('_analysis.json', '_graph.json')
                    graph_info = {}
                    if os.path.exists(graph_file):
                        with open(graph_file, 'r', encoding='utf-8') as f:
                            graph_data = json.load(f)
                            graph_info = {
                                'total_nodos': len(graph_data.get('nodes', {})),
                                'total_aristas': len(graph_data.get('edges', [])),
                                'metadata': graph_data.get('metadata', {})
                            }
                    
                    # Construir resultado para este archivo
                    results["resultados_detallados"][f"{base_name}.json"] = {
                        "graph_info": graph_info,
                        "threads_count": threads_count,
                        "analysis_summary": {
                            "total_hilos": analysis_data.get('thread_metrics', {}).get('total_threads', 0),
                            "hilo_promedio": analysis_data.get('thread_metrics', {}).get('avg_thread_length', 0),
                            "usuarios_activos": len(analysis_data.get('user_engagement', {}).get('most_active_users', [])),
                            "patrones_detectados": analysis_data.get('conversation_patterns', {}).get('total_conversation_patterns', 0)
                        }
                    }
                    
                    print(f"✅ Procesado: {base_name} - {threads_count} hilos")
                    
                except Exception as e:
                    print(f"❌ Error procesando {analysis_file}: {e}")
                    continue
            
            # Mostrar la ventana de resultados
            print("🪟 Abriendo ventana de resultados...")
            try:
                self.threads_results_window = ThreadsAnalysisResults(results, self)
                self.threads_results_window.show()
                self.threads_results_window.raise_()
                self.threads_results_window.activateWindow()
                print("✅ Ventana de resultados abierta correctamente")
            except Exception as e:
                print(f"❌ Error abriendo ventana de resultados: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo abrir la ventana de resultados: {str(e)}"
                )
            
        else:
            # Para otros tipos de análisis, mostrar el mensaje normal
            if successful and not failed:
                QMessageBox.information(
                    self,
                    "Descarga Completada",
                    f"Se descargaron exitosamente {len(successful)} chats:\n"
                    + "\n".join(successful[:10])
                    + (f"\n... y {len(successful) - 10} más" if len(successful) > 10 else ""),
                )
            elif successful and failed:
                QMessageBox.warning(
                    self,
                    "Descarga Parcial",
                    f"Exitosos ({len(successful)}):\n"
                    + "\n".join(successful[:5])
                    + (f"\n... y {len(successful) - 5} más" if len(successful) > 5 else "")
                    + f"\n\nFallaron ({len(failed)}):\n"
                    + "\n".join(failed[:5])
                    + (f"\n... y {len(failed) - 5} más" if len(failed) > 5 else ""),
                )
            elif failed and not successful:
                QMessageBox.critical(
                    self,
                    "Error en Descarga",
                    "Todos los chats fallaron:\n"
                    + "\n".join(failed[:10])
                    + (f"\n... y {len(failed) - 10} más" if len(failed) > 10 else ""),
                )

    def on_sentiment_analysis_completed(self, summary):
        # Abrir nueva ventana con el resumen
        dialog = SentimentAnalysisDialog(summary, self)
        dialog.exec()

    def on_conversation_threads_completed(self, results):
        """Manejar la finalización del análisis de hilos"""
        print("✅ Análisis de hilos completado, abriendo ventana de resultados...")
        
        # Cerrar el diálogo de progreso si existe
        if hasattr(self, 'threads_progress_dialog') and self.threads_progress_dialog:
            try:
                self.threads_progress_dialog.close()
                self.threads_progress_dialog = None
                print("✅ Diálogo de progreso cerrado")
            except Exception as e:
                print(f"❌ Error cerrando diálogo: {e}")
        
        # Habilitar botones nuevamente
        self.set_analysis_buttons_enabled(True)
        
        # Verificar si hay resultados válidos
        if not results:
            QMessageBox.warning(
                self, 
                "Análisis Completo", 
                "El análisis se completó pero no se generaron resultados."
            )
            return
            
        if not results.get('resultados_detallados'):
            QMessageBox.warning(
                self, 
                "Análisis Completo", 
                "El análisis se completó pero no se generaron resultados válidos.\n"
                "Esto puede deberse a que los chats no tienen conversaciones con respuestas."
            )
            return
        
        try:
            # Abrir la ventana de resultados
            print("🪟 Abriendo ventana de resultados...")
            self.threads_results_window = ThreadsAnalysisResults(results, self)
            self.threads_results_window.show()
            self.threads_results_window.raise_()  # Traer al frente
            self.threads_results_window.activateWindow()  # Activar ventana
            print("✅ Ventana de resultados abierta correctamente")
            
        except Exception as e:
            print(f"❌ Error abriendo ventana de resultados: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la ventana de resultados: {str(e)}"
            )

    def start_analysis(self, analysis_type):
        # Para análisis de hilos, permitir ejecutar sin chats seleccionados
        if analysis_type != "threads":
            selected_chats = []
            for widget in self.chat_widgets.values():
                selected_chats.extend(widget.get_selected_chats())

            if not selected_chats:
                QMessageBox.warning(
                    self, "Sin Selección", "Por favor, selecciona al menos un chat."
                )
                return
        else:
            # Para análisis de hilos, obtener chats seleccionados si los hay
            selected_chats = []
            for widget in self.chat_widgets.values():
                selected_chats.extend(widget.get_selected_chats())

        # Si es análisis de hilos y no hay chats seleccionados, cargar análisis existentes
        if analysis_type == "threads" and not selected_chats:
            self.load_existing_threads_analysis()
            return

        date_dialog = DateRangeDialog(self)
        if date_dialog.exec() == QDialog.DialogCode.Accepted:
            start_date, end_date = date_dialog.get_date_range()

            if start_date > end_date:
                QMessageBox.warning(
                    self,
                    "Error de Fechas",
                    "La fecha de inicio debe ser anterior a la fecha de fin.",
                )
                return

            media_dialog = MediaSelectionDialog(self)
            if media_dialog.exec() == QDialog.DialogCode.Accepted:
                media_options = media_dialog.get_selected_media()

                self.set_analysis_buttons_enabled(False)

                if self.worker.isRunning():
                    self.worker.wait()

                # Guardar el tipo de análisis para uso posterior
                self.analysis_type = analysis_type
                
                path = "."
                if analysis_type == "threads":
                    path = "./threads_analysis_results/chats"
                    # Crear directorio si no existe
                    os.makedirs(path, exist_ok=True)
                    # Mostrar diálogo de progreso
                    self.show_threads_progress_dialog()

                self.worker.set_task(
                    "download_chats",
                    selected_chats=selected_chats,
                    date_range=(start_date, end_date),
                    analysis_type=analysis_type,
                    media_options=media_options,
                    task_args={"path": path},
                )

                try:
                    self.worker.finished.disconnect()
                except Exception:
                    pass

                self.worker.finished.connect(lambda: self.set_analysis_buttons_enabled(True))
                self.worker.start()

    def load_existing_threads_analysis(self):
        """Cargar análisis de hilos existentes sin procesar chats nuevos"""
        print("🧵 Cargando análisis de hilos existentes...")
        
        # Buscar todos los archivos de análisis en threads_analysis_results/
        import glob
        analysis_files = glob.glob("threads_analysis_results/*_analysis.json")
        
        if not analysis_files:
            QMessageBox.warning(
                self, 
                "Análisis Completo", 
                "No se encontraron archivos de análisis existentes. Por favor, selecciona chats para analizar."
            )
            return
        
        print(f"📊 Encontrados {len(analysis_files)} archivos de análisis")
        
        # Construir resultados leyendo los archivos existentes
        results = {
            "archivos_procesados": len(analysis_files),
            "archivos_totales": len(analysis_files),
            "resultados_detallados": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for analysis_file in analysis_files:
            try:
                # Obtener el nombre base del archivo (sin _analysis.json)
                base_name = os.path.basename(analysis_file).replace('_analysis.json', '')
                print(f"📖 Leyendo análisis: {base_name}")
                
                # Cargar archivo de análisis
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                
                # Cargar archivo de hilos para contar hilos
                threads_file = analysis_file.replace('_analysis.json', '_threads.json')
                threads_count = 0
                if os.path.exists(threads_file):
                    with open(threads_file, 'r', encoding='utf-8') as f:
                        threads_data = json.load(f)
                        threads_count = len(threads_data.get('threads', {}))
                
                # Cargar archivo de grafo para obtener metadata
                graph_file = analysis_file.replace('_analysis.json', '_graph.json')
                graph_info = {}
                if os.path.exists(graph_file):
                    with open(graph_file, 'r', encoding='utf-8') as f:
                        graph_data = json.load(f)
                        graph_info = {
                            'total_nodos': len(graph_data.get('nodes', {})),
                            'total_aristas': len(graph_data.get('edges', [])),
                            'metadata': graph_data.get('metadata', {})
                        }
                
                # Construir resultado para este archivo
                results["resultados_detallados"][f"{base_name}.json"] = {
                    "graph_info": graph_info,
                    "threads_count": threads_count,
                    "analysis_summary": {
                        "total_hilos": analysis_data.get('thread_metrics', {}).get('total_threads', 0),
                        "hilo_promedio": analysis_data.get('thread_metrics', {}).get('avg_thread_length', 0),
                        "usuarios_activos": len(analysis_data.get('user_engagement', {}).get('most_active_users', [])),
                        "patrones_detectados": analysis_data.get('conversation_patterns', {}).get('total_conversation_patterns', 0)
                    }
                }
                
                print(f"✅ Procesado: {base_name} - {threads_count} hilos")
                
            except Exception as e:
                print(f"❌ Error procesando {analysis_file}: {e}")
                continue
        
        # Mostrar la ventana de resultados
        print("🪟 Abriendo ventana de resultados...")
        try:
            self.threads_results_window = ThreadsAnalysisResults(results, self)
            self.threads_results_window.show()
            self.threads_results_window.raise_()
            self.threads_results_window.activateWindow()
            print("✅ Ventana de resultados abierta correctamente")
        except Exception as e:
            print(f"❌ Error abriendo ventana de resultados: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la ventana de resultados: {str(e)}"
            )
    
    def show_threads_progress_dialog(self):
        """Mostrar diálogo de progreso para análisis de hilos"""
        self.threads_progress_dialog = QDialog(self)
        self.threads_progress_dialog.setWindowTitle("🔮 Construyendo Grafo de Conocimiento")
        self.threads_progress_dialog.setWindowIcon(QIcon("telegram_icon.png"))
        self.threads_progress_dialog.setModal(True)
        self.threads_progress_dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self.threads_progress_dialog)
        
        # Título y descripción
        title = QLabel("<h3 style='color: #2C6E91;'>Construyendo Grafo de Conocimiento</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        description = QLabel(
            "El sistema está analizando las conversaciones para reconstruir hilos...\n\n"
            "📊 Procesando:\n"
            "• Conexiones entre mensajes\n"
            "• Intenciones de conversación\n" 
            "• Patrones temporales\n"
            "• Relaciones sociales\n\n"
            "⏰ Esto puede tomar varios minutos dependiendo del tamaño del chat"
        )
        description.setWordWrap(True)
        description.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 10px;")
        layout.addWidget(description)
        
        # Spinner de carga
        spinner_label = QLabel("🔄 Procesando archivos...")
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner_label.setStyleSheet("font-size: 14px; color: #6c757d; padding: 20px;")
        layout.addWidget(spinner_label)
        
        # Botón para cancelar
        cancel_btn = QPushButton("Cerrar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_threads_analysis)
        layout.addWidget(cancel_btn)
        
        # Centrar en la pantalla
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.threads_progress_dialog.move(
            screen_geometry.center() - self.threads_progress_dialog.rect().center()
        )
        
        self.threads_progress_dialog.show()

    def cancel_threads_analysis(self):
        """Cancelar el análisis de hilos (solo cierra el diálogo)"""
        if hasattr(self, 'threads_progress_dialog') and self.threads_progress_dialog:
            try:
                self.threads_progress_dialog.close()
                self.threads_progress_dialog = None
            except:
                pass
    
    def set_analysis_buttons_enabled(self, enabled):
        self.total_analysis_btn.setEnabled(enabled)
        self.important_info_btn.setEnabled(enabled)
        self.conversation_threads_btn.setEnabled(enabled)

    def closeEvent(self, event):
        if hasattr(self, "worker"):
            self.worker.close_loop()
        event.accept()


