from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCalendarWidget,
    QDialogButtonBox,
    QCheckBox,
    QPushButton,
    QTextEdit,
    QMessageBox,
)
from PyQt6.QtCore import QDate, Qt
from datetime import datetime


class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Rango de Fechas")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Fecha de inicio:"))
        self.start_calendar = QCalendarWidget()
        self.start_calendar.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.start_calendar)

        layout.addWidget(QLabel("Fecha de fin:"))
        self.end_calendar = QCalendarWidget()
        self.end_calendar.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.end_calendar)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_date_range(self):
        start_qdate = self.start_calendar.selectedDate()
        end_qdate = self.end_calendar.selectedDate()

        start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day()).date()
        end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day()).date()

        return start, end


class MediaSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Tipos de Contenido")
        self.setModal(True)
        self.resize(300, 200)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Selecciona qué contenido descargar:</b>"))

        self.text_checkbox = QCheckBox("📄 Texto")
        self.text_checkbox.setChecked(True)
        self.text_checkbox.setEnabled(False)

        self.images_checkbox = QCheckBox("🖼️ Imágenes")
        self.audio_checkbox = QCheckBox("🎵 Audios")
        self.documents_checkbox = QCheckBox("📎 Documentos")

        layout.addWidget(self.text_checkbox)
        layout.addWidget(self.images_checkbox)
        layout.addWidget(self.audio_checkbox)
        layout.addWidget(self.documents_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selected_media(self):
        return {
            "text": True,
            "images": self.images_checkbox.isChecked(),
            "audio": self.audio_checkbox.isChecked(),
            "documents": self.documents_checkbox.isChecked(),
        }


class ChatPreviewDialog(QDialog):
    def __init__(self, chat_info, messages, worker_ref, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview — {chat_info.get('name')}")
        self.resize(700, 520)
        self.chat_info = chat_info
        self.messages = messages or []
        self.worker_ref = worker_ref

        layout = QVBoxLayout()

        opts_layout = QHBoxLayout()
        self.chk_images = QCheckBox("Imágenes")
        self.chk_docs = QCheckBox("Documentos")
        self.chk_audio = QCheckBox("Audio")
        self.chk_images.setChecked(False)
        self.chk_docs.setChecked(False)
        self.chk_audio.setChecked(False)
        opts_layout.addWidget(QLabel("Incluir:"), alignment=Qt.AlignmentFlag.AlignVCenter)
        opts_layout.addWidget(self.chk_images)
        opts_layout.addWidget(self.chk_docs)
        opts_layout.addWidget(self.chk_audio)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setStyleSheet("background: white; color: black;")
        layout.addWidget(self.preview_area)

        btn_row = QHBoxLayout()
        self.more_btn = QPushButton("Descargar más / Recargar")
        self.more_btn.clicked.connect(self.on_download_more)
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.close)
        btn_row.addStretch()
        btn_row.addWidget(self.more_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.render_messages(self.messages)

    def render_messages(self, messages):
        lines = []
        for m in messages:
            dt = m.get("date", "")
            sender = m.get("sender", "")
            text = m.get("text", "")
            media = m.get("media")
            media_line = ""
            if media and isinstance(media, dict):
                if media.get("downloaded"):
                    media_line = f" [Media: {media.get('filename', 'file')}]"
                else:
                    media_line = " [Media: no descargado]"

            lines.append(f"{dt} — {sender}: {text}{media_line}")
        self.preview_area.setPlainText("\n\n".join(lines) if lines else "Sin mensajes de preview.")

    def on_download_more(self):
        opts = {
            "text": True,
            "images": self.chk_images.isChecked(),
            "documents": self.chk_docs.isChecked(),
            "audio": self.chk_audio.isChecked(),
        }
        reply = QMessageBox.question(
            self,
            "Descargar contenidos",
            "Se descargarán los tipos seleccionados. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        parent = self.parent()
        try:
            if hasattr(parent, "preview_with_options"):
                parent.preview_with_options(self.chat_info, opts)
            else:
                QMessageBox.information(self, "No implementado", "Función de descarga no disponible.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo iniciar descarga: {e}")



