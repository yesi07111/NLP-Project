import os
import re
from pathlib import Path
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QSpinBox, QCheckBox,
    QGroupBox, QComboBox, QTextEdit, QMessageBox, QScrollArea,
    QFrame, QGridLayout, QDateEdit, QTimeEdit, QProgressDialog, QApplication,
    QDialogButtonBox
)

from PyQt6.QtCore import Qt, QTimer, QDate, QDateTime

# Importar configuración de regex
from regex.regex_config import (
    get_all_predefined_patterns, 
    get_social_media_patterns,
    get_ai_prompt_for_regex,
)

# Importar LinkProcessor
try:
    from link_processor.main import LinkProcessor
    HAS_LINK_PROCESSOR = True
except ImportError:
    HAS_LINK_PROCESSOR = False
    print("⚠️ LinkProcessor no disponible. Los enlaces se procesarán básicamente.")

try:
    import requests
    HAS_AI_API = True
    AI_PROVIDER = "openrouter"
except ImportError:
    HAS_AI_API = False
    AI_PROVIDER = None
    print("⚠️ requests es requerido: pip install requests")


class ExpandableSection(QGroupBox):
    """Grupo expandible/colapsable"""
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)  # Por defecto expandido
        self.toggled.connect(self.on_toggled)
        
    def on_toggled(self, checked):
        """Mostrar/ocultar contenido cuando se expande/colapsa"""
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                item.widget().setVisible(checked)


class AlarmConfigurationDialog(QDialog):
    def __init__(self, selected_chats, parent=None):
        super().__init__(parent)
        self.selected_chats = selected_chats
        self.alarm_configs = {}
        self.setWindowTitle("⚙️ Configurar Alarmas")
        # self.setMinimumSize(1200, 900)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            screen.left() + 50, 
            screen.top() + 50,
            screen.width() - 100,
            screen.height() - 100
        )

        # También agregar esta línea para permitir maximizar:
        self.setWindowFlags(
            self.windowFlags() | 
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
        # Asegurar que la ventana sea arrastrable
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
        self.setup_ui()
        self.center_dialog()
        
    def center_dialog(self):
        """Centra el diálogo en la pantalla"""
        screen_geometry = self.screen().availableGeometry()
        dialog_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        dialog_geometry.moveCenter(center_point)
        self.move(dialog_geometry.topLeft())
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("🔔 Configurar Alarmas Inteligentes")
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2ecc71);
            border-radius: 10px;
            color: white;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Descripción
        description = QLabel(
            "💡 Configura alarmas periódicas que analizarán mensajes y te enviarán resúmenes inteligentes. "
            "Las alarmas usarán IA para crear mensajes informativos y usarán expresiones regulares avanzadas."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            font-size: 14px; 
            color: #34495e; 
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        """)
        layout.addWidget(description)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #7f8c8d; margin: 10px 0;")
        layout.addWidget(separator)
        
        # Configuración de API de AI
        # Configuración de API de IA
        ai_config_group = QGroupBox("🤖 Configuración de IA (OpenRouter - Gratis)")
        ai_config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #9b59b6;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                padding-top: 20px;
            }
        """)
        
        ai_layout = QGridLayout()
        
        # # Info sobre OpenRouter
        # info_label = QLabel(
        #     "💡 <b>OpenRouter es GRATIS</b> con múltiples modelos<br>"
        #     "📊 Modelos gratis: Llama, Mistral, Gemma, Phi y más<br>"
        #     "🔑 Obtén tu clave gratis en: <a href='https://openrouter.ai/keys'>openrouter.ai/keys</a><br>"
        #     "💰 Crédito inicial: $1 gratis para probar"
        # )
        # info_label.setOpenExternalLinks(True)
        # info_label.setWordWrap(True)
        # info_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        # ai_layout.addWidget(info_label, 0, 0, 1, 3)
        
        ai_layout.addWidget(QLabel("Clave API:"), 0, 0)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Ej: sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.api_key_input.setStyleSheet("""
            padding: 10px; 
            border-radius: 5px; 
            border: 2px solid #bdc3c7;
            font-size: 13px;
        """)
        ai_layout.addWidget(self.api_key_input, 0, 1)
        
        # Cargar API key de archivo .env si existe
        self.load_api_key_from_env()
        
        ai_layout.addWidget(QLabel("Modelo:"), 1, 0)
        self.model_combo = QComboBox()
        self.load_available_models()
        self.model_combo.setCurrentIndex(0)  # Seleccionar el gratuito por defecto
        self.model_combo.setStyleSheet("""
            padding: 10px; 
            border-radius: 5px; 
            border: 2px solid #bdc3c7;
            font-size: 13px;
        """)

        self.model_combo.currentIndexChanged.connect(self.on_model_changed) 
        ai_layout.addWidget(self.model_combo, 1, 1)
        ai_layout.addWidget(self.model_combo, 1, 1)
        
        test_ai_btn = QPushButton("🔍 Probar Conexión IA")
        test_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        test_ai_btn.clicked.connect(self.test_ai_connection)
        ai_layout.addWidget(test_ai_btn, 0, 2)
        
        save_key_btn = QPushButton("💾 Guardar en .env")
        save_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        save_key_btn.clicked.connect(self.save_api_key_to_env)
        ai_layout.addWidget(save_key_btn, 1, 2)
        
        ai_config_group.setLayout(ai_layout)
        layout.addWidget(ai_config_group)
        
        # Tabs para cada chat
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: #ffffff;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 15px 30px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                color: #2c3e50;
                min-width: 150px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                border-bottom: 3px solid #2980b9;
            }
            QTabBar::tab:hover {
                background-color: #d6dbdf;
            }
        """)
        
        # Crear pestañas para cada chat seleccionado
        for chat in self.selected_chats:
            chat_widget = ChatAlarmConfigWidget(chat, self)
            chat_title = self.get_chat_title(chat)
            self.tab_widget.addTab(chat_widget, chat_title)
            
        layout.addWidget(self.tab_widget, 1)
        
        # Estadísticas
        stats_label = QLabel(f"📊 Configurando alarmas para {len(self.selected_chats)} chats seleccionados")
        stats_label.setStyleSheet("font-size: 13px; color: #7f8c8d; font-style: italic; padding: 10px;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("🚫 Cancelar")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                padding: 15px 30px;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.accept_btn = QPushButton("✅ Guardar Alarmas")
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #27ae60;
                padding: 15px 30px;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.accept_btn.clicked.connect(self.save_alarms)
        buttons_layout.addWidget(self.accept_btn)
        
        layout.addLayout(buttons_layout)
        
    def get_chat_title(self, chat):
        """Obtiene el título del chat de forma segura"""
        title = chat.get('name', 'Chat Desconocido')
        # Limitar longitud para la pestaña
        if len(title) > 25:
            title = title[:22] + '...'
        return title
    
    def load_api_key_from_env(self):
        """Cargar API key desde archivo .env"""
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if 'OPENROUTER_API_KEY=' in line:
                                key = line.split('=', 1)[1].strip()
                                if key and key != 'your_api_key_here':
                                    self.api_key_input.setText(key)
                                    print(f"✅ API Key cargada desde .env")
                                    return True
            except Exception as e:
                print(f"❌ Error cargando .env: {e}")
        return False
    
    def on_model_changed(self, index):
        """Mostrar info del modelo seleccionado"""
        model_name = self.model_combo.currentData()
        if not model_name:
            model_name = self.model_combo.currentText().replace('🆓', '').replace('💎', '').strip()
        
        is_free = 'flash' in model_name.lower()
        tooltip = f"Modelo: {model_name}\n"
        tooltip += "💰 Gratuito" if is_free else "💎 De pago"
        
        self.model_combo.setToolTip(tooltip)

    def save_api_key_to_env(self):
        """Guardar API key en archivo .env"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API Key vacía", "Por favor ingresa una API key válida")
            return
        
        env_file = Path('.env')
        try:
            lines = []
            key_found = False
            
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            
            # Buscar y reemplazar la línea_API_KEY
            for i, line in enumerate(lines):
                if line.strip().startswith('OPENROUTER_API_KEY='):
                    lines[i] = f'OPENROUTER_API_KEY={api_key}\n'
                    key_found = True
                    break
            
            # Si no se encontró, agregar al final
            if not key_found:
                lines.append(f'OPENROUTER_API_KEY={api_key}\n')
            
            # Escribir el archivo
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            # Establecer variable de entorno
            os.environ['_API_KEY'] = api_key
            
            QMessageBox.information(self, "✅ API Key guardada", 
                                  f"API key guardada en {env_file.absolute()}")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"No se pudo guardar la API key: {e}")
    
    def test_ai_connection(self):
        """Prueba la conexión con la API de IA"""
        if not HAS_AI_API:
            QMessageBox.warning(self, "API no disponible", 
                            "requests es requerido: pip install requests")
            return
        
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Clave API requerida", 
                            "Ingresa tu clave API de OpenRouter")
            return
        
        try:
            model_id = self.model_combo.currentData() or "meta-llama/llama-3.1-8b-instruct:free"
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "user", "content": "Di solo 'OK'"}
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                QMessageBox.information(
                    self, 
                    "✅ Conexión exitosa", 
                    f"OpenRouter API conectado correctamente\n\n"
                    f"✅ Modelo probado: {model_id}\n"
                    f"📝 Respuesta: {content}\n\n"
                    f"💡 Tienes acceso a múltiples modelos GRATIS"
                )
            else:
                error_data = response.json()
                QMessageBox.critical(
                    self,
                    "❌ Error de API",
                    f"Error {response.status_code}:\n\n{error_data.get('error', {}).get('message', str(error_data))}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "❌ Error de conexión", 
                f"No se pudo conectar:\n\n{str(e)}\n\n"
                f"Verifica tu clave API en:\n"
                f"https://openrouter.ai/keys"
            )
    
    def save_alarms(self):
        """Guarda todas las configuraciones de alarmas"""
        all_configs = []
        
        # Progreso
        progress = QProgressDialog("Guardando configuraciones...", "Cancelar", 0, len(self.selected_chats), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            progress.setLabelText(f"Procesando chat {i+1} de {len(self.selected_chats)}...")
            progress.setValue(i)
            
            if progress.wasCanceled():
                break
                
            config = widget.get_configuration()
            if config:
                all_configs.append(config)
            
            QApplication.processEvents()
        
        progress.setValue(len(self.selected_chats))
        
        if not all_configs:
            QMessageBox.warning(self, "Sin configuraciones", 
                              "No hay configuraciones válidas para guardar.")
            return
        
        # Guardar API key si se proporcionó
        api_key = self.api_key_input.text().strip()
        if api_key and HAS_AI_API:
            # Ya se guardó en .env con el botón, pero también configuramos la sesión actual
            try:
                # genai.configure(api_key=api_key)
                print("✅ AI configurado para esta sesión")
            except Exception as e:
                print(f"⚠️ Error configurando AI: {e}")
        
        self.alarm_configs = all_configs
        self.accept()
    
    def get_alarm_configurations(self):
        """Obtener todas las configuraciones de alarmas"""
        return self.alarm_configs

    def load_available_models(self):
        """Cargar modelos disponibles"""
        self.model_combo.clear()
        
        # Modelos gratuitos de OpenRouter
        free_models = [
            ("🆓 Meta Llama 3.1 8B (Rápido)", "meta-llama/llama-3.1-8b-instruct:free"),
            ("🆓 Meta Llama 3.2 3B (Ultra rápido)", "meta-llama/llama-3.2-3b-instruct:free"),
            ("🆓 Microsoft Phi-3 Medium", "microsoft/phi-3-medium-128k-instruct:free"),
            ("🆓 Microsoft Phi-3 Mini", "microsoft/phi-3-mini-128k-instruct:free"),
            ("🆓 Google Gemma 2 9B", "google/gemma-2-9b-it:free"),
            ("🆓 Mistral 7B", "mistralai/mistral-7b-instruct:free"),
            ("🆓 Qwen 2.5 7B", "qwen/qwen-2.5-7b-instruct:free"),
        ]
        
        print("\n📋 Modelos gratuitos disponibles en OpenRouter:")
        for label, model_id in free_models:
            self.model_combo.addItem(label, model_id)
            print(f"  ✅ {model_id}")
        
        print(f"✅ Cargados {len(free_models)} modelos gratuitos")
        self.model_combo.setCurrentIndex(0)
    

class ChatAlarmConfigWidget(QWidget):
    def __init__(self, chat_info, parent_dialog=None):
        super().__init__()
        self.chat_info = chat_info
        self.parent_dialog = parent_dialog
        self.regex_patterns = []
        self.custom_patterns = []
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Scroll area para contenido extenso
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Información del chat
        chat_info_group = QGroupBox(f"💬 Chat: {self.get_chat_title()}")
        chat_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #3498db;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding-top: 20px;
            }
        """)
        
        chat_layout = QGridLayout()
        chat_layout.addWidget(QLabel("ID del chat:"), 0, 0)
        chat_id_label = QLabel(str(self.chat_info.get('id', 'N/A')))
        chat_id_label.setStyleSheet("""
            font-family: 'Courier New'; 
            background-color: #f8f9fa; 
            padding: 8px;
            border-radius: 4px;
            font-size: 13px;
        """)
        chat_layout.addWidget(chat_id_label, 0, 1)
        
        chat_info_group.setLayout(chat_layout)
        layout.addWidget(chat_info_group)
        
        # Configuración del intervalo
        interval_group = ExpandableSection("⏰ Intervalo de Alarma")
        interval_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #e67e22;
                border: 2px solid #e67e22;
                border-radius: 8px;
                padding-top: 20px;
                min-height: 50px;
            }
        """)
        
        interval_layout = QGridLayout()
        interval_layout.setSpacing(20)
        interval_layout.setColumnStretch(1, 1)
        
        interval_layout.addWidget(QLabel("🔁 Repetir cada:"), 0, 0, 1, 4)
        
        # Fila 1: Meses y Días
        self.months_spin = self.create_spinbox(0, 12, "Meses")
        interval_layout.addWidget(self.months_spin, 1, 0)
        interval_layout.addWidget(QLabel("mes(es)"), 1, 1)
        
        self.days_spin = self.create_spinbox(0, 365, "Días", default=1)
        interval_layout.addWidget(self.days_spin, 1, 2)
        interval_layout.addWidget(QLabel("día(s)"), 1, 3)
        
        # Fila 2: Horas y Minutos
        self.hours_spin = self.create_spinbox(0, 23, "Horas", default=1)
        self.hours_spin.setMinimumHeight(50)
        interval_layout.addWidget(self.hours_spin, 2, 0)
        interval_layout.addWidget(QLabel("hora(s)"), 2, 1)
        
        self.minutes_spin = self.create_spinbox(0, 59, "Minutos", default=30)
        self.minutes_spin.setMinimumHeight(50)
        interval_layout.addWidget(self.minutes_spin, 2, 2)
        interval_layout.addWidget(QLabel("minuto(s)"), 2, 3)
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # Rango de fecha para primer análisis
        date_range_group = ExpandableSection("📅 Rango inicial de análisis")
        date_range_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #9b59b6;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                padding-top: 20px;
                min-height: 50px;
            }
        """)
        
        date_layout = QGridLayout()
        date_layout.setSpacing(15)
        date_layout.setColumnStretch(1, 1)
        
        date_layout.addWidget(QLabel("📅 Desde:"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setMinimumHeight(45)
        self.date_from.setStyleSheet("""
            QDateEdit {
                padding: 12px;
                border-radius: 6px;
                border: 2px solid #bdc3c7;
                font-size: 14px;
            }
            QDateEdit:hover {
                border-color: #3498db;
            }
        """)
        date_layout.addWidget(self.date_from, 0, 1)
        
        date_layout.addWidget(QLabel("⏰ Hora:"), 0, 2)
        self.time_from = QTimeEdit()
        self.time_from.setTime(QDateTime.currentDateTime().time())
        self.time_from.setMinimumHeight(45)
        self.time_from.setStyleSheet("""
            QTimeEdit {
                padding: 12px;
                border-radius: 6px;
                border: 2px solid #bdc3c7;
                font-size: 14px;
            }
            QTimeEdit:hover {
                border-color: #3498db;
            }
        """)
        date_layout.addWidget(self.time_from, 0, 3)
        
        date_layout.addWidget(QLabel("📅 Hasta:"), 1, 0)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumHeight(45)
        self.date_to.setStyleSheet("""
            QDateEdit {
                padding: 12px;
                border-radius: 6px;
                border: 2px solid #bdc3c7;
                font-size: 14px;
            }
            QDateEdit:hover {
                border-color: #3498db;
            }
        """)
        date_layout.addWidget(self.date_to, 1, 1)
        
        date_layout.addWidget(QLabel("⏰ Hora:"), 1, 2)
        self.time_to = QTimeEdit()
        self.time_to.setTime(QDateTime.currentDateTime().time())
        self.time_to.setMinimumHeight(45)
        self.time_to.setStyleSheet("""
            QTimeEdit {
                padding: 12px;
                border-radius: 6px;
                border: 2px solid #bdc3c7;
                font-size: 14px;
            }
            QTimeEdit:hover {
                border-color: #3498db;
            }
        """)
        date_layout.addWidget(self.time_to, 1, 3)
        
        date_range_group.setLayout(date_layout)
        layout.addWidget(date_range_group)
        
        # SECCIÓN DE PATRONES
        extract_group = QGroupBox("🔍 Información a Extraer")
        extract_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #2ecc71;
                border: 2px solid #2ecc71;
                border-radius: 8px;
                padding-top: 20px;
            }
        """)
        
        extract_layout = QVBoxLayout()
        
        # Obtener patrones predefinidos desde regex_config
        self.predefined_patterns = get_all_predefined_patterns()
        
        # Secciones plegables para categorías de patrones
        categories = {
            "📞 Contacto e Identificación": ["📧 Correos Electrónicos", "📞 Números de Teléfono"],
            "💸 Finanzas y Comercio": ["💰 Precios explícitos", "💰 Precios con $", "💰 Rangos de precios", "💳 Tarjetas de Crédito"],
            "🌐 Redes y Enlaces": ["🔗 URLs"] + list(get_social_media_patterns().keys())[:10],
            "📝 Contenido y Texto": ["#️⃣ Hashtags", "@️⃣ Menciones", "📊 Porcentajes"],
            "📍 Ubicación y Geografía": ["📍 Coordenadas", "🌐 Direcciones IP", "🚗 Placas de Vehículos"],
            "🔢 Códigos y Formatos": ["📚 Códigos ISBN", "₿ Direcciones Cripto"],
            "📅 Tiempo y Fechas": ["🗓️ Fechas absolutas", "🗓️ Fechas español", "📏 Medidas"],
        }
        
        # Crear secciones plegables para cada categoría
        self.category_sections = {}
        self.checkboxes = []  # Guardar referencias a los checkboxes
        
        for category_name, pattern_names in categories.items():
            section = ExpandableSection(category_name)
            section.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    color: #34495e;
                    border: 2px solid #95a5a6;
                    border-radius: 6px;
                    padding-top: 15px;
                    min-height: 40px;
                    margin-top: 10px;
                }
            """)
            
            section_layout = QVBoxLayout()
            section_layout.setSpacing(8)
            
            # Crear un layout de grid para los checkboxes (3 columnas)
            grid_layout = QGridLayout()
            grid_layout.setSpacing(12)
            
            col, row = 0, 0
            for pattern_name in pattern_names:
                if pattern_name in self.predefined_patterns:
                    cb = self.create_pattern_checkbox(pattern_name, self.predefined_patterns[pattern_name])
                    grid_layout.addWidget(cb, row, col)
                    self.checkboxes.append(cb)
                    col += 1
                    if col >= 3:  # 3 columnas
                        col = 0
                        row += 1
            
            section_layout.addLayout(grid_layout)
            section.setLayout(section_layout)
            extract_layout.addWidget(section)
            self.category_sections[category_name] = section
        
        # Opción personalizada
        custom_group = ExpandableSection("🎯 Patrones Personalizados (Regex o IA)")
        custom_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                color: #e74c3c;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                padding-top: 20px;
                min-height: 50px;
            }
        """)
        
        custom_layout = QVBoxLayout()
        custom_layout.setSpacing(15)
        
        custom_label = QLabel(
            "💡 <b>Instrucciones:</b><br>"
            "• Para <b>expresión regular propia</b>: escribe comenzando con <code>r''</code><br>"
            "• Para <b>pedido a IA</b>: describe lo que quieres extraer<br>"
            "• <b>Ejemplo regex:</b> <code>r'\\b\\d{3}-\\d{3}-\\d{4}\\b'</code><br>"
            "• <b>Ejemplo IA:</b> 'extraer números de serie de 10 dígitos'"
        )
        custom_label.setWordWrap(True)
        custom_label.setStyleSheet("""
            color: #34495e; 
            font-size: 13px; 
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px dashed #bdc3c7;
            min-height: 80px;
        """)
        custom_layout.addWidget(custom_label)
        
        # Área de texto más grande
        self.custom_input = QTextEdit()
        self.custom_input.setPlaceholderText(
            "Escribe aquí tus patrones personalizados...\n\n"
            "📌 EJEMPLOS DE EXPRESIONES REGULARES:\n"
            "r'\\b\\d{3}-\\d{3}-\\d{4}\\b'  # Teléfonos USA\n"
            "r'\\b[A-Z]{2}\\d{6}\\b'  # Códigos de producto\n"
            "r'\\b\\d{4}[A-Z]{2}\\b'  # Matrículas españolas\n\n"
            "📌 EJEMPLOS DE PEDIDOS A IA:\n"
            "extraer números de serie de 10 dígitos\n"
            "encontrar códigos postales de 5 dígitos\n"
            "detectar nombres de archivos .pdf o .docx\n"
            "buscar números de ticket como TKT-12345"
        )
        self.custom_input.setMinimumHeight(180)
        self.custom_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                font-family: 'Consolas', 'Monospace';
                min-height: 150px;
            }
            QTextEdit:focus {
                border-color: #2980b9;
            }
        """)
        custom_layout.addWidget(self.custom_input)
        
        # Botones para regex personalizados
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.add_regex_btn = QPushButton("➕ Añadir Regex Manual")
        self.add_regex_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 200px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.add_regex_btn.clicked.connect(self.add_custom_regex)
        buttons_layout.addWidget(self.add_regex_btn)
        
        self.generate_ai_btn = QPushButton("🤖 Generar con IA")
        self.generate_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 200px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.generate_ai_btn.clicked.connect(self.generate_ai_regex)
        buttons_layout.addWidget(self.generate_ai_btn)
        
        buttons_layout.addStretch()
        custom_layout.addLayout(buttons_layout)
        
        self.ai_status_label = QLabel("")
        self.ai_status_label.setStyleSheet("""
            color: #7f8c8d; 
            font-size: 12px; 
            font-style: italic; 
            padding: 8px;
            min-height: 30px;
        """)
        custom_layout.addWidget(self.ai_status_label)
        
        # Lista de patrones personalizados añadidos
        self.custom_patterns_label = QLabel("<b>📋 Patrones personalizados añadidos:</b>")
        self.custom_patterns_label.setStyleSheet("""
            color: #34495e; 
            font-size: 14px; 
            padding: 10px;
            min-height: 30px;
        """)
        custom_layout.addWidget(self.custom_patterns_label)
        
        self.custom_patterns_text = QTextEdit()
        self.custom_patterns_text.setReadOnly(True)
        self.custom_patterns_text.setMinimumHeight(180)
        self.custom_patterns_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #dcdde1;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #2c3e50;
                min-height: 150px;
            }
        """)
        custom_layout.addWidget(self.custom_patterns_text)
        
        # Botón para probar patrones
        test_buttons_layout = QHBoxLayout()
        test_buttons_layout.setSpacing(15)
        
        test_patterns_btn = QPushButton("🧪 Probar Todos los Patrones")
        test_patterns_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 250px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_patterns_btn.clicked.connect(self.test_all_patterns)
        test_buttons_layout.addWidget(test_patterns_btn)
        
        clear_btn = QPushButton("🗑️ Limpiar Personalizados")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                border: none;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        clear_btn.clicked.connect(self.clear_custom_patterns)
        test_buttons_layout.addWidget(clear_btn)
        
        test_buttons_layout.addStretch()
        custom_layout.addLayout(test_buttons_layout)
        
        custom_group.setLayout(custom_layout)
        extract_layout.addWidget(custom_group)
        
        extract_group.setLayout(extract_layout)
        layout.addWidget(extract_group)
        
        layout.addStretch()
        
        # Establecer el widget de contenido en el scroll
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def create_spinbox(self, min_val, max_val, placeholder, default=0):
        """Crea un spinbox con estilo consistente"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setMinimumHeight(50)
        spinbox.setStyleSheet("""
            QSpinBox {
                padding: 12px;
                border-radius: 8px;
                border: 2px solid #bdc3c7;
                font-size: 14px;
                min-width: 100px;
            }
            QSpinBox:hover {
                border-color: #3498db;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 25px;
                height: 20px;
            }
        """)
        return spinbox
    
    def create_pattern_checkbox(self, name, pattern):
        """Crea un checkbox para patrón con estilo"""
        cb = QCheckBox(name)
        cb.pattern = pattern
        cb.pattern_name = name
        cb.setChecked(True)  # Por defecto seleccionados
        cb.setMinimumHeight(25)
        cb.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                padding: 8px;
                spacing: 10px;
                min-height: 25px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #bdc3c7;
            }
            QCheckBox::indicator:checked {
                background-color: #2ecc71;
                border-color: #27ae60;
            }
            QCheckBox::indicator:hover {
                border-color: #3498db;
            }
        """)
        return cb
    
    def get_chat_title(self):
        """Obtiene el título del chat"""
        title = self.chat_info.get('name', 'Chat Desconocido')
        return title
    
    def add_custom_regex(self):
        """Añade regex personalizado manualmente"""
        custom_text = self.custom_input.toPlainText().strip()
        
        if not custom_text:
            QMessageBox.warning(self, "Sin entrada", 
                              "Por favor ingresa una expresión regular o una descripción.")
            return
        
        # Separar por líneas
        lines = custom_text.split('\n')
        added_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Verificar si es una expresión regular (comienza con r' o r")
            if line.startswith("r'") or line.startswith('r"'):
                # Es una regex explícita
                try:
                    # Extraer el patrón entre comillas
                    if line.startswith("r'"):
                        pattern = line[2:-1] if line.endswith("'") else line[2:]
                    else:
                        pattern = line[2:-1] if line.endswith('"') else line[2:]
                    
                    # Compilar para validar
                    compiled = re.compile(pattern)
                    
                    self.add_pattern_to_list(pattern, "Manual", line)
                    added_count += 1
                    
                except re.error as e:
                    QMessageBox.warning(self, "Regex inválida", 
                                      f"La expresión regular no es válida:\n{line}\n\nError: {e}")
                    return
            else:
                # Es una descripción para IA
                QMessageBox.information(self, "Descripción detectada", 
                                      f"'{line[:50]}...'\n\nUsa el botón 'Generar con IA' para convertir esta descripción en una expresión regular.")
        
        if added_count > 0:
            self.custom_input.clear()
            self.ai_status_label.setText(f"✅ Añadidas {added_count} expresiones regulares")
            QTimer.singleShot(3000, lambda: self.ai_status_label.clear())
    
    def generate_ai_regex(self):
        """Genera regex usando AI"""
        description = self.custom_input.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(self, "Sin descripción", 
                              "Por favor describe qué quieres extraer.")
            return
        
        # Verificar si hay API key disponible
        api_key = None
        if self.parent_dialog and hasattr(self.parent_dialog, 'api_key_input'):
            api_key = self.parent_dialog.api_key_input.text().strip()
        
        if not api_key and HAS_AI_API:
            # Intentar variable de entorno
            api_key = os.getenv('_API_KEY')
        
        if not api_key:
            QMessageBox.warning(self, "API Key requerida", 
                              "Necesitas una clave API de AI para usar IA.\n\n"
                              "1. Obtén una clave en: https://makersuite.com/app/apikey\n"
                              "2. Instala: pip install-generativeai\n"
                              "3. Configúrala en el campo superior o en variable de entorno_API_KEY")
            return
        
        # Mostrar estado
        self.ai_status_label.setText("⏳ Generando expresión regular con IA...")
        self.generate_ai_btn.setEnabled(False)
        
        # Usar QTimer para no bloquear la UI
        QTimer.singleShot(100, lambda: self._call_ai_api(description, api_key))
    

    def _call_ai_api(self, description, api_key):
        """Llama a la API de IA para generar regex"""
        try:
            model_id = self.parent_dialog.model_combo.currentData() or "meta-llama/llama-3.1-8b-instruct:free"
            prompt = get_ai_prompt_for_regex(description)
            
            print(f"🤖 Usando modelo: {model_id}")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": "Eres un experto en expresiones regulares. Responde SOLO con la expresión regular, sin explicaciones."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                },
                timeout=30
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            result = response.json()
            regex_result = result['choices'][0]['message']['content'].strip()
            
            # Limpiar respuesta
            regex_result = regex_result.strip("'\"` \n")
            # Quitar bloques de código markdown
            if '```' in regex_result:
                regex_result = regex_result.split('```')[1]
                if regex_result.startswith('regex\n') or regex_result.startswith('python\n'):
                    regex_result = '\n'.join(regex_result.split('\n')[1:])
            if regex_result.startswith('r"') or regex_result.startswith("r'"):
                regex_result = regex_result[2:-1]
            
            # Validar
            try:
                re.compile(regex_result)
                self.add_pattern_to_list(regex_result, "OpenRouter AI", description)
                self.custom_input.clear()
                self.ai_status_label.setText("✅ Regex generado exitosamente")
            except re.error as e:
                self.ai_status_label.setText("❌ Error en regex generado")
                QMessageBox.warning(self, "Regex inválida", 
                                f"La IA generó una regex inválida:\n\n{regex_result}\n\nError: {e}")
                
        except Exception as e:
            self.ai_status_label.setText("❌ Error de conexión")
            QMessageBox.critical(self, "Error de IA", f"No se pudo generar:\n\n{str(e)}")
        finally:
            self.generate_ai_btn.setEnabled(True)
            QTimer.singleShot(5000, lambda: self.ai_status_label.clear())

    def add_pattern_to_list(self, pattern, source, description=None):
        """Añade un patrón a la lista de patrones personalizados"""
        # Añadir a la lista interna
        self.custom_patterns.append({
            "pattern": pattern,
            "source": source,
            "description": description or pattern,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Actualizar el texto visible
        current_text = self.custom_patterns_text.toPlainText()
        if current_text:
            current_text += "\n"
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M")
        display_desc = description[:40] + "..." if description and len(description) > 40 else description
        
        current_text += f"# [{timestamp}] {source}: {display_desc}\nr'{pattern}'\n"
        self.custom_patterns_text.setText(current_text)
    
    def clear_custom_patterns(self):
        """Limpia todos los patrones personalizados"""
        if not self.custom_patterns:
            return
        
        reply = QMessageBox.question(self, "Confirmar limpieza", 
                                    f"¿Estás seguro de que quieres eliminar {len(self.custom_patterns)} patrones personalizados?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.custom_patterns_text.clear()
            self.custom_patterns.clear()
            self.ai_status_label.setText("🗑️ Patrones eliminados")
            QTimer.singleShot(3000, lambda: self.ai_status_label.clear())
    
    def test_all_patterns(self):
        """Prueba TODOS los patrones seleccionados"""
        # Crear diálogo personalizado para texto más grande
        dialog = QDialog(self)
        dialog.setWindowTitle("🧪 Probar Patrones")
        dialog.setMinimumSize(700, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Ingresa texto para probar todos los patrones seleccionados:")
        label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(label)
        
        self.test_text_edit = QTextEdit()
        self.test_text_edit.setPlainText(
            "Hola, mi correo es usuario@example.com y mi teléfono es +34 600 123 456.\n"
            "También tengo otro: +1-800-555-1234.\n"
            "El precio del producto es $100 USD con un 20% de descuento.\n"
            "Visita nuestro sitio: https://ejemplo.com y síguenos en @usuario.\n"
            "Coordenadas: 40.4168, -3.7038 #viaje #madrid\n"
            "Fecha de la reunión: 15/12/2023 a las 14:30.\n"
            "Número de tarjeta: 4111-1111-1111-1111 (solo ejemplo).\n"
            "Dirección IP: 192.168.1.1\n"
            "Código ISBN: 978-3-16-148410-0"
        )
        self.test_text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 15px;
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: white;
            }
        """)
        layout.addWidget(self.test_text_edit)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        text = self.test_text_edit.toPlainText().strip()
        
        if not text:
            return
        
        # Resto del código de prueba (se mantiene igual hasta la sección de mostrar resultados)
        results = []
        found_count = 0
        
        # Probar patrones predefinidos seleccionados
        for cb in self.checkboxes:
            if cb.isChecked():
                try:
                    matches = re.findall(cb.pattern, text, re.IGNORECASE)
                    if matches:
                        count = len(matches)
                        found_count += count
                        # Filtrar duplicados
                        unique_matches = list(dict.fromkeys(matches))
                        examples = unique_matches[:3]
                        examples_str = ', '.join(str(e) for e in examples)
                        if count > 3:
                            examples_str += f" y {count-3} más"
                        results.append(f"✅ {cb.pattern_name}: {count} encontrados → {examples_str}")
                    else:
                        results.append(f"❌ {cb.pattern_name}: 0 encontrados")
                except re.error as e:
                    results.append(f"❌ {cb.pattern_name}: Error en patrón → {str(e)}")
        
        # Probar patrones personalizados
        for i, custom in enumerate(self.custom_patterns):
            try:
                matches = re.findall(custom['pattern'], text, re.IGNORECASE)
                if matches:
                    count = len(matches)
                    found_count += count
                    unique_matches = list(dict.fromkeys(matches))
                    examples = unique_matches[:2]
                    examples_str = ', '.join(str(e) for e in examples)
                    if count > 2:
                        examples_str += f" y {count-2} más"
                    source = custom.get('source', 'Personalizado')
                    results.append(f"✅ {source} {i+1}: {count} encontrados → {examples_str}")
                else:
                    results.append(f"❌ Personalizado {i+1}: 0 encontrados")
            except re.error as e:
                results.append(f"❌ Personalizado {i+1}: Error en patrón → {str(e)}")
        
        # Mostrar resultados en diálogo más grande
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("📊 Resultados de Prueba")
        result_dialog.setMinimumSize(800, 500)
        
        result_layout = QVBoxLayout(result_dialog)
        
        # Crear widget con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Resumen
        summary = QLabel(f"📊 RESULTADOS DE PRUEBA\n"
                        f"Texto analizado: {len(text)} caracteres\n"
                        f"Total de coincidencias: {found_count}\n"
                        f"Patrones probados: {len(self.checkboxes) + len(self.custom_patterns)}")
        summary.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            padding: 15px;
            background-color: #e8f4fc;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        """)
        content_layout.addWidget(summary)
        
        # Resultados detallados
        if results:
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setPlainText("\n".join(results))
            results_text.setStyleSheet("""
                QTextEdit {
                    font-family: 'Consolas', monospace;
                    font-size: 11px;
                    padding: 10px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    background-color: white;
                }
            """)
            content_layout.addWidget(results_text)
        else:
            no_results = QLabel("⚠️ No se encontraron coincidencias con los patrones seleccionados.")
            no_results.setStyleSheet("color: #e74c3c; padding: 20px; font-size: 13px;")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(no_results)
        
        scroll.setWidget(content)
        result_layout.addWidget(scroll)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(result_dialog.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 30px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        result_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        result_dialog.exec()
        
    def get_configuration(self):
        """Obtener configuración completa para este chat"""
        # Obtener patrones predefinidos seleccionados
        selected_patterns = []
        
        # Buscar checkboxes seleccionados
        for cb in self.checkboxes:
            if cb.isChecked():
                selected_patterns.append({
                    "name": cb.pattern_name,
                    "pattern": cb.pattern,
                    "type": "predefined"
                })
        
        # Agregar patrones personalizados
        for i, custom in enumerate(self.custom_patterns):
            selected_patterns.append({
                "name": f"Personalizado {i+1}",
                "pattern": custom['pattern'],
                "type": "custom",
                "source": custom['source'],
                "description": custom['description']
            })
        
        if not selected_patterns:
            QMessageBox.warning(self, "Sin patrones", 
                              "Por favor selecciona al menos un patrón para extraer.")
            return None
        
        # Validar intervalo
        total_minutes = (
            self.months_spin.value() * 30 * 24 * 60 +  # meses a minutos
            self.days_spin.value() * 24 * 60 +         # días a minutos
            self.hours_spin.value() * 60 +             # horas a minutos
            self.minutes_spin.value()                  # minutos
        )
        
        if total_minutes < 1:
            QMessageBox.warning(self, "Intervalo inválido", 
                              "El intervalo debe ser de al menos 1 minuto.")
            return None
        
        # Crear objetos datetime para el rango
        from_datetime = QDateTime(
            self.date_from.date(),
            self.time_from.time()
        ).toPyDateTime()
        
        to_datetime = QDateTime(
            self.date_to.date(),
            self.time_to.time()
        ).toPyDateTime()
        
        # Validar rango de fechas
        if from_datetime > to_datetime:
            QMessageBox.warning(self, "Rango inválido", 
                              "La fecha 'Desde' debe ser anterior a 'Hasta'.")
            return None
        
        # Configuración final
        config = {
            "chat_id": self.chat_info.get('id'),
            "chat_title": self.get_chat_title(),
            "chat_username": self.chat_info.get('username', ''),
            "interval": {
                "months": self.months_spin.value(),
                "days": self.days_spin.value(),
                "hours": self.hours_spin.value(),
                "minutes": self.minutes_spin.value(),
                "total_minutes": total_minutes
            },
            "date_range": {
                "from": from_datetime.isoformat(),
                "to": to_datetime.isoformat()
            },
            "patterns": selected_patterns,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_analyzed_message_id": None,
            "last_analysis_time": None,
            "total_runs": 0,
            "enabled": True
        }
        
        return config