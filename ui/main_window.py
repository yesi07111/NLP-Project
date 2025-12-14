#main_window.py
import sys
import os
import json
from datetime import datetime
import threading

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QStackedWidget, QMessageBox, QTabWidget,
    QProgressBar,
)

from PyQt6.QtGui import (
    QIcon, QFont, QPixmap, QColor
)

from PyQt6.QtCore import (
    Qt, QTimer
)
import schedule
from telethon import TelegramClient

from config.settings import API_ID, API_HASH, SESSION_NAME
from telegram.async_worker import AsyncWorker
from ui.alarm_configuration_dialog import AlarmConfigurationDialog
from ui.widgets import ChatListWidget
from ui.dialogs import DateRangeDialog, MediaSelectionDialog, ChatPreviewDialog
from ui.threads_results_view import ThreadsAnalysisResults
from telegram.alarm_manager import AlarmConfig, AlarmManager


class TelegramApp(QWidget):
    send_to_saved_messages_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asistente de Telegram")
        self.setGeometry(300, 150, 620, 620)
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

        # Inicializar gestor de alarmas
        self.alarm_manager = None
        self.alarm_monitor_thread = None
        self.chats_updated = pyqtSignal(dict)
         # Conectar la señal
        self.send_to_saved_messages_signal.connect(self.handle_send_to_saved_messages)

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
        title.setWordWrap(False)
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
        self.refresh_worker = None

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
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)

        # ================= TOP BAR =================
        top_layout = QHBoxLayout()

        title_label = QLabel("<h3 style='color:#2C6E91;'>Tus Chats y Grupos</h3>")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        self.logout_btn = QPushButton("🔒 Cerrar Sesión")
        self.logout_btn.setFixedHeight(35)
        self.logout_btn.setStyleSheet(
            "QPushButton { background-color:#dc3545; color:white; padding:8px 12px; border-radius:6px; font-size:12px; }"
            "QPushButton:hover { background-color:#c82333; }"
        )
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)

        self.refresh_btn = QPushButton("🔄 Actualizar mensajes")
        self.refresh_btn.setStyleSheet(
            "QPushButton { background-color:#0d6efd; color:white; padding:8px 16px; border-radius:6px; font-weight:bold; }"
            "QPushButton:hover { background-color:#0b5ed7; }"
        )
        self.refresh_btn.clicked.connect(self.force_refresh_chats)
        top_layout.addWidget(self.refresh_btn)

        chat_layout.addLayout(top_layout)

        # ================= CHAT TABS =================
        self.chat_tabs = QTabWidget()
        self.chat_widgets = {}

        for name, key in [
            ("Todos", "todos"),
            ("No Leídos", "no_leídos"),
            ("Personales", "personales"),
            ("Grupos", "grupos"),
        ]:
            widget = ChatListWidget()
            self.chat_widgets[key] = widget
            self.chat_tabs.addTab(widget, name)

        chat_layout.addWidget(self.chat_tabs)

        # ================= ANALYSIS LABEL =================
        chat_layout.addWidget(QLabel("<b>Herramientas de Análisis:</b>"))

        # ================= GRID DE BOTONES (2x2) =================
        buttons_container = QVBoxLayout()
        buttons_container.setSpacing(6)

        # ---------- FILA 1 ----------
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.threads_analysis_btn = QPushButton("💬 Análisis de Hilos")
        self.threads_analysis_btn.clicked.connect(lambda: self.start_analysis("threads"))
        self.threads_analysis_btn.setStyleSheet(
            "QPushButton { background-color:#6f42c1; color:white; padding:12px; border-radius:6px; font-weight:bold; }"
            "QPushButton:hover { background-color:#5a359a; }"
        )

        self.configure_alarms_btn = QPushButton("⏰ Configurar Alarmas")
        self.configure_alarms_btn.clicked.connect(self.open_alarm_configuration)
        self.configure_alarms_btn.setStyleSheet(
            "QPushButton { background-color:#007bff; color:white; padding:12px; border-radius:6px; font-weight:bold; }"
            "QPushButton:hover { background-color:#0056b3; }"
        )

        row1.addWidget(self.threads_analysis_btn, 1)
        row1.addWidget(self.configure_alarms_btn, 1)

        # ---------- FILA 2 ----------
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        test_alarm_btn = QPushButton("🧪 Probar Alarma")
        test_alarm_btn.clicked.connect(self.test_alarm_functionality)
        test_alarm_btn.setStyleSheet(
            "QPushButton { background-color:#ff5555; color:white; padding:12px; border-radius:6px; font-weight:bold; }"
            "QPushButton:hover { background-color:#cc0000; }"
        )

        view_status_btn = QPushButton("📊 Ver Estado Alarmas")
        view_status_btn.clicked.connect(self.show_alarm_status)
        view_status_btn.setStyleSheet(
            "QPushButton { background-color:#3498db; color:white; padding:12px; border-radius:6px; font-weight:bold; }"
            "QPushButton:hover { background-color:#1a5a8a; }"
        )

        row2.addWidget(test_alarm_btn, 1)
        row2.addWidget(view_status_btn, 1)

        buttons_container.addLayout(row1)
        buttons_container.addLayout(row2)

        chat_layout.addLayout(buttons_container)

        # ================= PROGRESS =================
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        chat_layout.addWidget(self.progress_bar)

        self.user_info_label = QLabel("")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setStyleSheet("color:#666; font-size:11px;")
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
        self.worker.conversation_threads_completed.connect(self.on_conversation_threads_completed) # Nueva señal
        self.worker.chats_loaded.connect(self.on_chats_loaded)

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
            self.refresh_btn.setEnabled(True)
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

    def force_refresh_chats(self):
        """Forzar recarga de chats y mensajes desde Telegram"""
        try:
            # Evitar lanzar otro refresh si ya hay uno corriendo
            self.refresh_btn.setEnabled(False)
            if self.refresh_worker and self.refresh_worker.isRunning():
                print("⚠️ Ya hay una actualización de chats en curso")
                return

            print("🔄 Forzando actualización de chats...")

            self.refresh_worker = self.create_worker()
            self.refresh_worker.set_task("load_chats")

            # Cuando termine, liberar referencia
            self.refresh_worker.finished.connect(self._on_refresh_finished)

            self.refresh_worker.start()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo actualizar los mensajes:\n{e}"
            )

    def _on_refresh_finished(self):
        print("✅ Actualización de chats finalizada")
        self.refresh_worker = None


    def show_chat_screen_directly(self):
        self.stack.setCurrentWidget(self.chat_screen)
        QTimer.singleShot(100, self.load_chats_delayed)
        # Inicializar AlarmManager con el cliente del worker
        QTimer.singleShot(200, self.initialize_alarm_manager) 
    
    def initialize_alarm_manager(self):
        """Inicializar AlarmManager con el cliente activo"""
        if not self.alarm_manager and hasattr(self, 'worker'):
            try:
                print("🔄 Inicializando AlarmManager con cliente activo...")
                
                # Asegurar que el worker tenga cliente
                if not hasattr(self.worker, 'client') or not self.worker.client:
                    print("⚠️ Worker sin cliente, esperando...")
                    return
                
                self.alarm_manager = AlarmManager(
                    telegram_client=self.worker.client,
                    telegram_app=self
                )
                print("✅ AlarmManager inicializado con cliente existente")
            except Exception as e:
                print(f"⚠️ Error inicializando AlarmManager: {e}")
                import traceback
                traceback.print_exc()

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

    # def show_preview_dialog(self, chat_info, messages, worker):
    #     try:
    #         dlg = ChatPreviewDialog(chat_info, messages, worker_ref=worker, parent=self)
    #         dlg.exec()
    #     except Exception as e:
    #         QMessageBox.warning(self, "Error", f"No se pudo abrir la vista previa: {e}")

    def show_preview_dialog(self, chat_info, messages, worker):
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QLabel, QPushButton,
            QScrollArea, QWidget, QHBoxLayout
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Vista previa — {chat_info['name']}")
        dialog.setMinimumSize(900, 600)

        # Centrar y agrandar
        screen = QApplication.primaryScreen().availableGeometry()
        dialog.setGeometry(
            screen.left() + 80,
            screen.top() + 80,
            screen.width() - 160,
            screen.height() - 160
        )

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ================= HEADER =================
        header = QLabel(f"💬 {chat_info['name']}")
        header.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2C6E91;
                padding: 8px;
            }
        """)
        main_layout.addWidget(header)

        # ================= SCROLL =================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f4f6f8;
            }
        """)

        container = QWidget()
        messages_layout = QVBoxLayout(container)
        messages_layout.setSpacing(10)
        messages_layout.setContentsMargins(10, 10, 10, 10)

        # ================= MENSAJES =================
        for msg in reversed(messages):  # más antiguos arriba
            bubble = QWidget()
            bubble_layout = QVBoxLayout(bubble)
            bubble_layout.setContentsMargins(12, 8, 12, 8)

            sender = msg.get("sender", "Usuario")
            date = msg.get("date", "")
            text = msg.get("text", "")

            sender_label = QLabel(sender)
            sender_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #495057;
                    font-size: 12px;
                }
            """)

            text_label = QLabel(text or "<i>(mensaje vacío)</i>")
            text_label.setWordWrap(True)
            text_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    color: #212529;
                }
            """)

            date_label = QLabel(date)
            date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            date_label.setStyleSheet("""
                QLabel {
                    font-size: 10px;
                    color: #868e96;
                }
            """)

            bubble_layout.addWidget(sender_label)
            bubble_layout.addWidget(text_label)
            bubble_layout.addWidget(date_label)

            bubble.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 10px;
                    border: 1px solid #dee2e6;
                }
            """)

            messages_layout.addWidget(bubble)

        messages_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        QTimer.singleShot(
            0,
            lambda: scroll.verticalScrollBar().setValue(
                scroll.verticalScrollBar().maximum()
            )
        )


        # ================= FOOTER =================
        footer = QHBoxLayout()
        footer.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        close_btn.clicked.connect(dialog.accept)

        footer.addWidget(close_btn)
        footer.addStretch()
        main_layout.addLayout(footer)

        dialog.exec()


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
        
        # Cargar o generar el resumen de sentimientos
        summary_file = "threads_analysis_results/global_sentiment_summary.json"
        summary = {}
        
        if os.path.exists(summary_file):
            print("📊 Cargando análisis de sentimientos existente...")
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                print("✅ Análisis de sentimientos cargado")
            except Exception as e:
                print(f"⚠️  Error cargando análisis de sentimientos: {e}")
                summary = self.generate_sentiment_summary_from_chats()
        else:
            print("📊 Generando análisis de sentimientos...")
            summary = self.generate_sentiment_summary_from_chats()
            
            # Guardar el resumen para uso futuro
            try:
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                print(f"✅ Resumen de sentimientos guardado en {summary_file}")
            except Exception as e:
                print(f"⚠️  Error guardando resumen de sentimientos: {e}")
        
        # Agregar el resumen a los resultados
        results["resumen_sentimientos"] = summary
        
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

    def generate_sentiment_summary_from_chats(self):
        """Generar resumen de sentimientos a partir de los chats existentes"""
        import glob
        from utils.sentiments.sentiment_analysis import get_sentiment_summary
        
        # Buscar archivos JSON en la carpeta threads_analysis_results/chats/
        chat_files = glob.glob("threads_analysis_results/chats/*.json")
        
        if not chat_files:
            print("⚠️  No se encontraron archivos de chat")
            return {
                "total_messages": 0,
                "average_score": 0.0,
                "most_common_sentiment": "N/A",
                "distribution": {},
                "percentages": {},
                "user_sentiments": {}
            }
        
        print(f"📁 Encontrados {len(chat_files)} archivos de chat para análisis de sentimientos")
        
        # Acumular todos los mensajes de todos los archivos
        all_messages = []
        
        for chat_file in chat_files:
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    all_messages.extend(messages)
                    print(f"📄 {os.path.basename(chat_file)}: {len(messages)} mensajes")
            except Exception as e:
                print(f"❌ Error leyendo {chat_file}: {e}")
                continue
        
        if not all_messages:
            print("⚠️  No hay mensajes para analizar")
            return {
                "total_messages": 0,
                "average_score": 0.0,
                "most_common_sentiment": "N/A",
                "distribution": {},
                "percentages": {},
                "user_sentiments": {}
            }
        
        print(f"📊 Analizando {len(all_messages)} mensajes en total...")
        
        # Generar resumen de sentimientos
        summary = get_sentiment_summary(all_messages)
        
        print(f"✅ Análisis de sentimientos completado: {summary.get('total_messages', 0)} mensajes analizados")
        
        return summary

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
        self.threads_analysis_btn.setEnabled(enabled)
        self.configure_alarms_btn.setEnabled(enabled)
    
    def open_alarm_configuration(self):
        """Abrir diálogo de configuración de alarmas"""
        # Obtener chats seleccionados
        selected_chats = []
        for widget in self.chat_widgets.values():
            selected_chats.extend(widget.get_selected_chats())

        if not selected_chats:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, selecciona al menos un chat para configurar alarmas."
            )
            return

        # Abrir diálogo de configuración de alarmas
        dialog = AlarmConfigurationDialog(selected_chats, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            alarm_configs = dialog.get_alarm_configurations()
            # Iniciar las alarmas
            self.setup_alarms(alarm_configs)

    def save_alarm_configurations(self, alarm_configs):
        """Guardar configuración de alarmas en archivo"""
        try:
            config_dir = "alarm_configurations"
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, "alarm_settings.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "alarm_configs": alarm_configs,
                    "created_at": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving alarm configurations: {e}")

    def send_immediate_alarms(self, alarm_configs):
        """Enviar alarmas inmediatas a mensajes guardados"""
        # Esta función debería usar el worker para enviar mensajes
        # Por ahora solo muestra un mensaje de ejemplo
        print(f"Sending immediate alarms for {len(alarm_configs)} chats")

    def schedule_periodic_alarms(self, alarm_configs):
        """Programar alarmas periódicas usando QTimer"""
        # Esta función configuraría QTimer para cada alarma
        print(f"Scheduling periodic alarms for {len(alarm_configs)} chats")
        
    def handle_send_to_saved_messages(self, message: str):
        """Manejar el envío de mensajes a mensajes guardados"""
        try:
            # Crear worker para enviar el mensaje
            worker = self.create_worker()
            worker.set_task("send_message", message=message)
            worker.start()
        except Exception as e:
            print(f"❌ Error manejando envío a mensajes guardados: {e}")
    
    def show_alarm_status(self):
        """Mostrar estado de las alarmas activas"""
        if not self.alarm_manager or not self.alarm_manager.alarms:
            QMessageBox.information(self, "Estado de Alarmas", 
                                "No hay alarmas configuradas actualmente.\n"
                                "Usa 'Configurar Alarmas' para crear nuevas.")
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
        
        status_dialog = QDialog(self)
        status_dialog.setWindowTitle("📊 Estado de Alarmas")
        
        # Hacer la ventana más grande
        screen = QApplication.primaryScreen().availableGeometry()
        status_dialog.setGeometry(
            screen.left() + 100,
            screen.top() + 100,
            screen.width() - 200,
            screen.height() - 200
        )
        
        layout = QVBoxLayout(status_dialog)
        
        # Obtener estado actualizado usando get_alarm_status() que devuelve diccionarios
        try:
            alarm_status = self.alarm_manager.get_alarm_status()
            
            if not alarm_status:
                layout.addWidget(QLabel("No hay alarmas activas"))
            else:
                table = QTableWidget()
                table.setColumnCount(8)
                table.setHorizontalHeaderLabels([
                    "ID", "Chat", "Estado", "Ejecuciones",
                    "Próxima", "Tiempo Restante", "Patrones", "Acciones"
                ])
                
                table.setRowCount(len(alarm_status))
                
                for i, status in enumerate(alarm_status):
                    alarm_id = status['id']

                    table.setItem(i, 0, QTableWidgetItem(str(alarm_id)))

                    chat_item = QTableWidgetItem(status['title'])
                    chat_item.setToolTip(f"ID: {alarm_id}")
                    table.setItem(i, 1, chat_item)

                    status_text = "✅ Activa" if status['enabled'] else "⏸️ Pausada"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setForeground(QColor('#27ae60') if status['enabled'] else QColor('#e74c3c'))
                    table.setItem(i, 2, status_item)

                    runs_item = QTableWidgetItem(str(status['total_runs']))
                    runs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(i, 3, runs_item)

                    table.setItem(i, 4, QTableWidgetItem(status['next_run']))
                    table.setItem(i, 5, QTableWidgetItem(status['time_left']))

                    patterns_item = QTableWidgetItem(str(status['patterns']))
                    table.setItem(i, 6, patterns_item)

                    # 🔴 Botón eliminar
                    delete_btn = QPushButton("🗑 Eliminar")
                    delete_btn.setMinimumHeight(36)
                    delete_btn.setMinimumWidth(120)
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e74c3c;
                            color: white;
                            border-radius: 6px;
                            padding: 8px 16px;
                            font-weight: bold;
                            font-size: 13px;
                        }
                        QPushButton:hover {
                            background-color: #c0392b;
                        }
                    """)

                    delete_btn.clicked.connect(
                        lambda _, aid=alarm_id: self._delete_alarm_and_refresh(aid, status_dialog)
                    )

                    table.setCellWidget(i, 7, delete_btn)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setAlternatingRowColors(True)
                table.setStyleSheet("""
                    QTableWidget {
                        background-color: #f8f9fa;
                        alternate-background-color: #e9ecef;
                        gridline-color: #dee2e6;
                    }
                    QTableWidget::item {
                        padding: 12px;
                        border-bottom: 1px solid #dee2e6;
                        font-size: 13px;
                    }
                    QTableWidget::item:selected {
                        background-color: #3498db;
                        color: white;
                    }
                """)
                
                layout.addWidget(table)
                
        except Exception as e:
            error_label = QLabel(f"Error cargando estado: {str(e)}")
            error_label.setStyleSheet("color: #e74c3c; padding: 20px;")
            layout.addWidget(error_label)
        
        # Botón para cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(status_dialog.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 40px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Agregar botón en un layout centrado
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        status_dialog.exec()

    def setup_alarms(self, alarm_configs):
        """Configurar y programar las alarmas"""
        try:
            if not self.alarm_manager:
                print("🔄 Inicializando AlarmManager...")
                
                # SIEMPRE usar el cliente del worker activo
                if not hasattr(self.worker, 'client') or not self.worker.client:
                    QMessageBox.warning(
                        self,
                        "Cliente no disponible",
                        "No hay un cliente de Telegram activo.\n"
                        "Por favor, recarga los chats primero."
                    )
                    return
                
                client = self.worker.client
                print("✅ Usando cliente existente del worker")
                
                # Crear AlarmManager con el cliente
                self.alarm_manager = AlarmManager(
                    telegram_client=client,
                    telegram_app=self
                )
                print("✅ AlarmManager inicializado")
            
            # Añadir cada alarma al gestor
            alarm_ids = []
            for config in alarm_configs:
                try:
                    alarm_id = self.alarm_manager.add_alarm(config)
                    if alarm_id:
                        alarm_ids.append(alarm_id)
                        print(f"✅ Alarma {alarm_id} configurada para: {config['chat_title']}")
                    else:
                        print(f"⚠️ No se pudo configurar alarma para: {config['chat_title']}")
                except Exception as e:
                    print(f"❌ Error configurando alarma: {e}")
                    continue
            
            if not alarm_ids:
                QMessageBox.warning(
                    self,
                    "Sin alarmas configuradas",
                    "No se pudo configurar ninguna alarma. Verifica los logs."
                )
                return
            
            # Iniciar monitoreo de alarmas
            self.start_alarm_monitoring()
            
            # Iniciar monitoreo de chats
            self.start_chat_monitoring()
            
            # Iniciar timer de actualización UI
            self.start_ui_refresh_timer()
            QMessageBox.information(
                self,
                "✅ Alarmas Configuradas",
                f"Se han configurado {len(alarm_ids)} alarmas.\n\n"
                "Las alarmas se ejecutarán automáticamente según los intervalos configurados.\n"
                "Los resúmenes se enviarán a tus Mensajes Guardados en Telegram.\n\n"
                "Los chats están siendo monitoreados para detectar nuevos mensajes."
            )
            
            # Mostrar estado actual de alarmas
            self.show_alarm_status()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"No se pudieron configurar las alarmas: {str(e)}\n\n"
                f"Detalles: {type(e).__name__}"
            )
            import traceback
            traceback.print_exc()

    def _delete_alarm_and_refresh(self, alarm_id, dialog):
        confirm = QMessageBox.question(
            self,
            "Eliminar alarma",
            f"¿Eliminar la alarma {alarm_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.alarm_manager.remove_alarm(alarm_id)
            self.alarm_manager.save_alarms()
            dialog.accept()
            self.show_alarm_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la alarma:\n{e}")


    def start_alarm_monitoring(self):
        """Iniciar monitoreo de alarmas y cambios en chats"""
        if self.alarm_monitor_thread and self.alarm_monitor_thread.is_alive():
            print("✅ Monitoreo ya está activo")
            return
        
        def monitor_alarms():
            import time
            while True:
                try:
                    # Revisar y ejecutar alarmas pendientes
                    if self.alarm_manager:
                        # Ejecutar jobs programados
                        schedule.run_pending()
                    
                    # Refrescar lista de chats periódicamente (cada 60 segundos)
                    time.sleep(60)
                    
                    # Opcional: recargar chats para ver cambios si no hay monitoreo activo
                    if (hasattr(self, 'worker') and not self.worker.isRunning() and 
                        self.has_active_session and not self.is_chat_monitoring_active()):
                        print("🔄 Refrescando lista de chats...")
                        self.worker = self.create_worker()
                        self.worker.set_task("load_chats")
                        self.worker.start()
                        
                except Exception as e:
                    print(f"⚠️ Error en monitoreo: {e}")
                    time.sleep(10)
        
        self.alarm_monitor_thread = threading.Thread(
            target=monitor_alarms, 
            daemon=True,
            name="AlarmMonitor"
        )
        self.alarm_monitor_thread.start()
        print("🚀 Monitoreo de alarmas iniciado")
        
        # También iniciar monitoreo de chats si hay alarmas configuradas
        if self.alarm_manager and self.alarm_manager.alarms:
            self.start_chat_monitoring()

    def start_ui_refresh_timer(self):
        """Iniciar timer para refrescar UI cada minuto"""
        if not hasattr(self, 'ui_refresh_timer'):
            self.ui_refresh_timer = QTimer()
            self.ui_refresh_timer.timeout.connect(self.refresh_chats_ui)
            self.ui_refresh_timer.start(60000)  # 60000 ms = 1 minuto
            print("⏰ Timer de actualización UI iniciado (cada 1 minuto)")
    
    def refresh_chats_ui(self):
        """Refrescar lista de chats sin bloquear UI"""
        if not self.has_active_session:
            return
        
        # Solo refrescar si no hay operaciones en curso
        if hasattr(self, 'worker') and not self.worker.isRunning():
            print("🔄 Refrescando lista de chats...")
            self.worker = self.create_worker()
            self.worker.set_task("load_chats")
            self.worker.start()

    def is_chat_monitoring_active(self):
        """Verificar si el monitoreo de chats está activo"""
        # Verificar si hay alarmas activas con monitoreo
        if not hasattr(self, 'alarm_manager') or not self.alarm_manager:
            return False
        
        # Si hay alarmas activas, el monitoreo está activo
        if self.alarm_manager.alarms:
            for alarm in self.alarm_manager.alarms.values():
                if alarm.enabled:
                    return True
        
        return False

    def start_chat_monitoring(self):
        """Iniciar monitoreo de chats con alarmas"""
        if not self.alarm_manager or not self.alarm_manager.alarms:
            print("⚠️ No hay alarmas para monitorear")
            return
        
        # Obtener IDs de chats con alarmas activas
        chat_ids = []
        for alarm_id, alarm in self.alarm_manager.alarms.items():
            if alarm.enabled:
                chat_ids.append(alarm.chat_id)
                print(f"📡 Monitoreando chat: {alarm.chat_title} (ID: {alarm.chat_id})")
        
        if not chat_ids:
            print("⚠️ No hay chats habilitados para monitoreo")
            return
        
        # Si ya hay un monitor_worker vivo en self, no crear otro
        existing_monitor = getattr(self, "monitor_worker", None)
        if existing_monitor and existing_monitor.isRunning():
            print("⚠️ El monitor de chats ya está en ejecución")
            return
        
        # Preferir reutilizar el worker principal si existe y no está ocupado
        main_worker = getattr(self, "worker", None)
        try_reuse_main = False
        if main_worker:
            try:
                # Solo reutilizar si no está ejecutándose (evita pisar tareas activas)
                if not main_worker.isRunning():
                    try_reuse_main = True
            except Exception:
                try_reuse_main = False
        
        if try_reuse_main:
            # Reutilizar worker principal
            monitor_worker = main_worker
            monitor_worker.set_task("monitor_chats", task_args={'chat_ids': chat_ids})
            # conectar señales para logging y limpieza (no duplicar conexiones)
            def _on_success(msg):
                print(f"✅ Monitor worker (principal): {msg}")
            def _on_error(err):
                print(f"❌ Error en monitor worker (principal): {err}")
            try:
                monitor_worker.success.connect(_on_success)
                monitor_worker.error.connect(_on_error)
            except Exception:
                pass
            monitor_worker.start()
            self.monitor_worker = monitor_worker
            print(f"✅ Monitoreo iniciado para {len(chat_ids)} chats (reutilizando worker principal)")
            return
        
        # Si no podemos reutilizar el worker principal, crear uno persistente en self
        self.monitor_worker = self.create_worker()
        self.monitor_worker.set_task("monitor_chats", task_args={'chat_ids': chat_ids})
        
        # Conectar manejadores para logging y limpieza al terminar
        def on_monitor_success(msg):
            print(f"✅ Monitor worker: {msg}")
        def on_monitor_error(err):
            print(f"❌ Error en monitor worker: {err}")
        def on_monitor_finished():
            print("🛑 Monitor worker finalizado")
            try:
                self.monitor_worker.success.disconnect(on_monitor_success)
            except Exception:
                pass
            try:
                self.monitor_worker.error.disconnect(on_monitor_error)
            except Exception:
                pass
            try:
                self.monitor_worker.finished.disconnect(on_monitor_finished)
            except Exception:
                pass
            # liberar referencia para evitar QThread: Destroyed while running
            try:
                self.monitor_worker = None
            except Exception:
                pass
        
        try:
            self.monitor_worker.success.connect(on_monitor_success)
            self.monitor_worker.error.connect(on_monitor_error)
            self.monitor_worker.finished.connect(on_monitor_finished)
        except Exception:
            pass
        
        # Iniciar el worker (no usar threading.Thread; QThread.start() ya crea su hilo)
        self.monitor_worker.start()
        print(f"✅ Monitoreo iniciado para {len(chat_ids)} chats")


    def closeEvent(self, event):
        """Cerrar aplicación correctamente"""
        try:
            # Detener alarm manager
            if hasattr(self, 'alarm_manager') and self.alarm_manager:
                print("🛑 Deteniendo AlarmManager...")
                self.alarm_manager.stop()
            
            # Detener timer de UI
            if hasattr(self, 'ui_refresh_timer'):
                self.ui_refresh_timer.stop()
            
            # Detener worker
            if hasattr(self, "worker"):
                if self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait(2000)  # Esperar máximo 2 segundos
                self.worker.close_loop()
        except Exception as e:
            print(f"Error cerrando aplicación: {e}")
        finally:
            event.accept()

    def test_alarm_functionality(self):
        """Probar la funcionalidad de alarmas enviando un mensaje de prueba"""
        try:
            print("🧪 Iniciando prueba de alarma...")
            
            # Crear mensaje de prueba
            from datetime import datetime
            test_message = (
                "✅ PRUEBA DE ALARMA\n\n"
                "Este es un mensaje de prueba enviado a Mensajes Guardados.\n"
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                "Estado: Sistema de alarmas funcionando correctamente.\n\n"
                "📢 Las alarmas configuradas te enviarán resúmenes periódicos."
            )
            
            # Asegurarnos de tener el worker existente
            if not hasattr(self, 'worker') or not self.worker:
                QMessageBox.warning(self, "Worker no disponible", "No hay worker de Telegram disponible.")
                return
            
            client = getattr(self.worker, 'client', None)
            loop = getattr(self.worker, 'loop', None)
            
            # 1) Si el worker ya tiene un loop corriendo, usarlo para enviar el mensaje directamente
            if client and loop and getattr(loop, "is_running", lambda: False)():
                import asyncio
                
                print("📤 Enviando mensaje usando el loop del worker existente...")
                future = asyncio.run_coroutine_threadsafe(client.send_message("me", test_message), loop)
                
                def _on_done(fut):
                    try:
                        res = fut.result()
                        print(f"✅ Mensaje enviado exitosamente (ID: {getattr(res, 'id', '<sin id>')})")
                        # Emitir señales (si están conectadas) y mostrar diálogo en GUI
                        try:
                            self.worker.success.emit("✅ Mensaje enviado a Mensajes Guardados")
                        except Exception:
                            pass
                        QTimer.singleShot(0, lambda: QMessageBox.information(
                            self,
                            "✅ Prueba Exitosa",
                            "Se ha enviado un mensaje de prueba a tus Mensajes Guardados.\n\n"
                            "Verifica en Telegram → Mensajes Guardados"
                        ))
                    except Exception as e:
                        print(f"❌ Error en prueba: {e}")
                        try:
                            self.worker.error.emit(str(e))
                        except Exception:
                            pass
                        QTimer.singleShot(0, lambda: QMessageBox.critical(
                            self,
                            "❌ Error en Prueba",
                            f"No se pudo enviar la prueba:\n\n{e}"
                        ))
                
                future.add_done_callback(_on_done)
                return
            
            # 2) Si el worker NO tiene loop corriendo, intentar arrancar el propio worker para ejecutar la tarea
            # (esto reutiliza self.worker y evita crear otro worker que desconecte el client compartido)
            if not getattr(self.worker, "isRunning", lambda: False)():
                print("🚀 Configurando el worker existente para enviar el mensaje de prueba...")
                
                # Conectar manejadores temporales (se desconectan después en los handlers)
                def on_test_success(msg):
                    print(f"✅ Prueba exitosa: {msg}")
                    try:
                        self.worker.success.disconnect(on_test_success)
                    except Exception:
                        pass
                    try:
                        self.worker.error.disconnect(on_test_error)
                    except Exception:
                        pass
                    QMessageBox.information(
                        self,
                        "✅ Prueba Exitosa",
                        "Se ha enviado un mensaje de prueba a tus Mensajes Guardados.\n\n"
                        "Verifica en Telegram → Mensajes Guardados"
                    )
                
                def on_test_error(err):
                    print(f"❌ Error en prueba: {err}")
                    try:
                        self.worker.success.disconnect(on_test_success)
                    except Exception:
                        pass
                    try:
                        self.worker.error.disconnect(on_test_error)
                    except Exception:
                        pass
                    QMessageBox.critical(
                        self,
                        "❌ Error en Prueba",
                        f"No se pudo enviar la prueba:\n\n{err}"
                    )
                
                try:
                    self.worker.success.connect(on_test_success)
                    self.worker.error.connect(on_test_error)
                except Exception:
                    # si conectar falla, seguimos adelante pero sin handlers temporales
                    pass
                
                # Setear la tarea y arrancar el worker (el worker usará su propia lógica para asegurarse conexión)
                self.worker.set_task("send_message", task_args={'message': test_message})
                self.worker.start()
                print("🚀 Worker de prueba iniciado.")
                return
            
            # 3) Si llegamos aquí, el worker existe pero está ocupado
            QMessageBox.warning(self, "Worker ocupado", "El worker está ocupado. Intenta de nuevo en unos segundos.")
            
        except Exception as e:
            error_msg = f"Error en prueba: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "❌ Error", error_msg)


    def update_chat_unread_count(self, chat_id):
        """Actualizar contador de no leídos para un chat específico"""
        # Esta función busca el chat en todos los widgets y actualiza su contador
        for tab_key, widget in self.chat_widgets.items():
            for i in range(widget.count()):
                item = widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    chat_info = item.data(Qt.ItemDataRole.UserRole)
                    if chat_info.get('id') == chat_id:
                        # Incrementar contador de no leídos
                        chat_info['unread_count'] = chat_info.get('unread_count', 0) + 1
                        item.setText(f"{chat_info['name']} ({chat_info['unread_count']})")
                        break
    
    def handle_new_message(self, chat_id, message_data):
        """Manejar nuevo mensaje recibido en tiempo real"""
        print(f"🔄 Actualizando UI para nuevo mensaje en chat {chat_id}")
        
        # Actualizar contador de no leídos
        self.update_chat_unread_count(chat_id)
        
        # Verificar si hay alarmas para este chat
        if self.alarm_manager:
            for alarm_id, alarm in self.alarm_manager.alarms.items():
                if alarm.chat_id == chat_id and alarm.enabled:
                    print(f"⚠️ Alarma {alarm_id} detectó nuevo mensaje en chat monitoreado")
                    # Aquí podrías activar la alarma inmediatamente si lo deseas
                    # self.alarm_manager.queue_alarm(alarm_id)
        
        # Opcional: mostrar notificación
        self.show_message_notification(chat_id, message_data)

    def show_message_notification(self, chat_id, message_data):
        """Mostrar notificación de nuevo mensaje"""
        # Buscar nombre del chat
        chat_name = f"Chat {chat_id}"
        for tab_key, widget in self.chat_widgets.items():
            for i in range(widget.count()):
                item = widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    chat_info = item.data(Qt.ItemDataRole.UserRole)
                    if chat_info.get('id') == chat_id:
                        chat_name = chat_info.get('name', chat_name)
                        break
        
        # Mostrar notificación en la barra de estado
        message_preview = message_data.get('text', '')[:50]
        notification = f"📨 Nuevo mensaje en {chat_name}: {message_preview}..."
        
        # Puedes usar QSystemTrayIcon para notificaciones del sistema
        # Por ahora, solo imprimir en consola
        print(f"🔔 {notification}")





