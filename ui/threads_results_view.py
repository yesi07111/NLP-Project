import os
import json
import math
from datetime import datetime
import networkx as nx

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget,
    QScrollArea, QComboBox, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QTextEdit,
    QSizePolicy, QFrame, QGraphicsPolygonItem, QLineEdit, QGridLayout,
    QGroupBox
)

from PyQt6.QtGui import (
    QIcon, QFont, QPen, QBrush, QColor, QPainter, QPolygonF
)

from PyQt6.QtCore import (
    Qt, QTimer, QRectF, QPointF
)


class ThreadsAnalysisResults(QMainWindow):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.USER_COLORS = [
              "#dcf8c6", "#fff3b0", "#ffd6a5", "#caffbf", "#9bf6ff",
            "#a0c4ff", "#bdb2ff", "#ffadad", "#ffd6e0", "#e0bbff",
            "#c1fba4", "#bffdec", "#fffdaf", "#d2f5e3", "#ffecda",
            "#d7e3fc", "#f3d0ff", "#d0f4de", "#ffcad4", "#e2f0cb"
        ]
        self.user_id_to_name = {}  # Mapeo de ID a nombre de usuario
        self.current_chat_index = 0
        self.current_thread_index = 0
        self.chat_data = self.load_chat_data()
        self.setWindowTitle("🔮 Análisis de Conversaciones - Vista de Hilos")
        self.setGeometry(100, 50, 1400, 900)
        self.setWindowIcon(QIcon("telegram_icon.png"))
        self.setup_ui()
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                border: none;
                padding: 12px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                color: #495057;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #2C6E91;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #ced4da;
            }
        """)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Tabs principales
        self.tab_widget = QTabWidget()
        
        self.resumen_tab = self.create_resumen_tab()
        self.hilos_tab = self.create_hilos_tab()
        self.grafo_tab = self.create_grafo_tab()
        self.feelings_tab = self.create_sentiment_analysis_tab(self.results["resumen_sentimientos"])
        self.analisis_tab = self.create_analisis_tab()
        
        self.tab_widget.addTab(self.resumen_tab, "📊 Resumen")
        self.tab_widget.addTab(self.hilos_tab, "💬 Hilos")
        self.tab_widget.addTab(self.grafo_tab, "🕸️ Grafos")
        self.tab_widget.addTab(self.feelings_tab, "😊 Sentimientos")
        self.tab_widget.addTab(self.analisis_tab, "📈 Análisis")
        
        layout.addWidget(self.tab_widget)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2C6E91, stop:1 #6f42c1);
            border-radius: 15px;
            padding: 15px;
        """)
        layout = QHBoxLayout(header)
        
        title = QLabel("🧠 Análisis de Conversaciones")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        subtitle = QLabel("Reconstrucción inteligente de hilos usando Grafos de Conocimiento")
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.9);")
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(subtitle)
        
        return header

    def create_resumen_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Métricas principales
        metrics = self.create_metrics_cards()
        layout.addWidget(metrics)
        
        # Lista de chats
        chats_list = self.create_chats_list()
        layout.addWidget(chats_list)
        
        return widget

    def create_metrics_cards(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        
        resultados = self.results.get('resultados_detallados', {})
        total_chats = len(resultados)
        
        # Calcular métricas agregadas
        total_hilos = sum(r['analysis_summary']['total_hilos'] for r in resultados.values())
        total_mensajes = sum(r['graph_info']['total_nodos'] for r in resultados.values())
        total_conexiones = sum(r['graph_info']['total_aristas'] for r in resultados.values())
        
        # Calcular usuarios únicos
        usuarios_unicos = 0
        for r in resultados.values():
            usuarios_unicos += (r.get('analysis_summary', {}).get('usuarios_activos', 0))
        
        cards_data = [
            ("📁", "Chats Analizados", f"{total_chats}", "#2C6E91", "Total de conversaciones procesadas"),
            ("💬", "Hilos Detectados", f"{total_hilos}", "#28a745", "Conversaciones reconstruidas"),
            ("👥", "Usuarios Únicos", f"{usuarios_unicos}", "#6f42c1", "Participantes diferentes"),
            ("🔗", "Conexiones", f"{total_conexiones}", "#fd7e14", "Relaciones identificadas")
        ]
        
        for icon, title, value, color, desc in cards_data:
            card = self.create_metric_card(icon, title, value, color, desc)
            layout.addWidget(card)
        
        return widget

    def create_metric_card(self, icon, title, value, color, description):
        card = QWidget()
        card.setMinimumHeight(140)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 white, stop:1 #f8f9fa);
                border: 2px solid {color};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(card)
        
        # Header
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("font-size: 14px; color: #495057;")
        
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        
        # Value
        value_label = QLabel(f"<h1 style='color: {color}; margin: 10px 0; font-size: 32px;'>{value}</h1>")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; text-align: center; margin-top: 5px;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(header)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        
        return card

    def create_chats_list(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("<h3 style='color: #2C6E91; margin-bottom: 10px;'>📋 Chats Analizados</h3>")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)
        
        resultados = self.results.get('resultados_detallados', {})
        for i, (archivo, datos) in enumerate(resultados.items()):
            chat_card = self.create_chat_card(archivo, datos, i)
            content_layout.addWidget(chat_card)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget

    def create_chat_card(self, archivo, datos, index):
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 0px;
            }
            QWidget:hover {
                border: 2px solid #2C6E91;
                background: #f8f9fa;
            }
        """)
        layout = QVBoxLayout(card)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        #TODO
        chat_name = datos.get('graph_info', {}).get('metadata', {}).get('metadata', {}).get('chat_name', 'Chat Desconocido')
        if not chat_name or chat_name == 'Chat':
            chat_name = archivo.replace('.json', '').replace('_', ' ')
        
        icon = QLabel("💬")
        name = QLabel(f"<b>{chat_name}</b>")
        name.setStyleSheet("font-size: 14px; color: #2C6E91;")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(name)
        header_layout.addStretch()
        
        # Stats
        stats = QHBoxLayout()
        
        analisis = datos.get('analysis_summary', {})
        stats_data = [
            (f"🧵 {analisis.get('total_hilos', 0)}", "hilos"),
            (f"👥 {analisis.get('usuarios_activos', 0)}", "usuarios"),
            (f"📊 {datos['graph_info']['total_nodos']}", "mensajes"),
            (f"🔗 {datos['graph_info']['total_aristas']}", "conexiones")
        ]
        
        for value, label in stats_data:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #495057;")
            label_label = QLabel(label)
            label_label.setStyleSheet("font-size: 9px; color: #6c757d;")
            
            stat_layout.addWidget(value_label)
            stat_layout.addWidget(label_label)
            stats.addWidget(stat_widget)
        
        layout.addWidget(header)
        layout.addLayout(stats)
        
        # Hacer clickable
        card.mousePressEvent = lambda e, idx=index: self.select_chat(idx)
        
        return card

    def select_chat(self, index):
        self.current_chat_index = index
        self.tab_widget.setCurrentIndex(1)  # Ir a pestaña de hilos
        self.load_chat_threads()

    def create_hilos_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de control de hilos
        control_bar = QWidget()
        control_bar.setFixedHeight(80)
        control_bar.setStyleSheet("background: white; border-bottom: 2px solid #e0e0e0; padding: 10px;")
        control_layout = QHBoxLayout(control_bar)
        
        # Chat selector
        self.chat_selector = QComboBox()
        self.chat_selector.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #2C6E91;
                border-radius: 8px;
                font-weight: bold;
                min-width: 250px;
                min-height: 40px;
                font-size: 14px;
            }
        """)
        
        # Navegación de hilos
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setSpacing(10)
        
        self.prev_btn = QPushButton("◀ Anterior")
        self.next_btn = QPushButton("Siguiente ▶")
        
        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedHeight(45)
            btn.setMinimumWidth(120)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2C6E91;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #3A88B1;
                }
                QPushButton:disabled {
                    background: #cccccc;
                    color: #666666;
                }
            """)
        
        self.thread_info = QLabel("Selecciona un chat")
        self.thread_info.setStyleSheet("font-weight: bold; color: #2C6E91; padding: 0 20px; font-size: 14px;")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.thread_info)
        nav_layout.addWidget(self.next_btn)
        
        control_layout.addWidget(QLabel("<b>Chat:</b>"))
        control_layout.addWidget(self.chat_selector)
        control_layout.addStretch()
        control_layout.addWidget(nav_widget)
        
        # Contenedor principal centrado para la conversación
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de conversación
        self.conversation_area = QScrollArea()
        self.conversation_area.setWidgetResizable(True)
        self.conversation_area.setMaximumWidth(800)
        self.conversation_area.setStyleSheet("""
            QScrollArea {
                background: #e5ddd5;
                border: none;
            }
        """)
        
        self.conversation_widget = QWidget()
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.setSpacing(8)
        self.conversation_layout.setContentsMargins(20, 10, 20, 10)
        
        self.conversation_area.setWidget(self.conversation_widget)
        
        # Centrar el área de conversación
        center_layout.addStretch()
        center_layout.addWidget(self.conversation_area)
        center_layout.addStretch()
        
        layout.addWidget(control_bar)
        layout.addWidget(center_widget)
        
        # Conectar señales
        self.chat_selector.currentIndexChanged.connect(self.on_chat_selected)
        self.prev_btn.clicked.connect(self.previous_thread)
        self.next_btn.clicked.connect(self.next_thread)
        
        # Cargar datos iniciales
        self.load_chat_selector()
        
        return widget

    def load_thread(self, thread_index):
        """Carga un hilo con color único por usuario"""
        self.clear_conversation()

        if thread_index >= len(self.threads):
            return

        thread_id = list(self.threads.keys())[thread_index]
        thread = self.threads[thread_id]
        messages = thread.get('messages', [])

        # Filtrar mensajes vacíos
        valid_messages = [
            msg for msg in messages
            if msg.get("text") and msg["text"].strip() and len(msg["text"].strip()) > 1
        ]
        messages = valid_messages

        # Ordenar mensajes
        def parse_timestamp(ts):
            try:
                if "T" in ts:
                    if ts.endswith("Z"):
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return datetime.fromisoformat(ts)
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except:
                return datetime.min

        messages.sort(key=lambda x: parse_timestamp(x.get("timestamp", "")))

        # Color único por usuario
        user_colors = {}
        next_color_index = 0

        # Determinar el usuario principal
        if not hasattr(self, "primary_user_id") or self.primary_user_id is None:
            ids = [m.get("user_id") for m in messages if m.get("user_id") not in ("Sistema", None)]
            if ids:
                self.primary_user_id = max(set(ids), key=ids.count)
            else:
                self.primary_user_id = None

        for i, msg in enumerate(messages):
            user_id = msg.get("user_id", "Sistema")

            if user_id not in user_colors and user_id != "Sistema":
                user_colors[user_id] = self.USER_COLORS[next_color_index % len(self.USER_COLORS)]
                next_color_index += 1

            bubble_color = user_colors.get(user_id, "#fff9c4")

            # Alineación correcta
            if user_id == "Sistema":
                alignment = "center"
            elif user_id == self.primary_user_id:
                alignment = "right"
            else:
                alignment = "left"

            self.add_message_bubble(msg, alignment, True, bubble_color)

        # Navegación
        self.thread_info.setText(f"Hilo {thread_index + 1} de {self.total_threads}")
        self.prev_btn.setEnabled(thread_index > 0)
        self.next_btn.setEnabled(thread_index < self.total_threads - 1)

        QTimer.singleShot(100, self.scroll_to_bottom)

    def add_message_bubble(self, msg, alignment, show_username=True, bubble_color="#ffffff"):
        """Añade una burbuja con color único por usuario."""
        user_id = msg.get("user_id", "Sistema")
        text = msg.get("text", "Sin texto") or "Sin texto"
        text = text.strip()
        timestamp = msg.get("timestamp", "")

        # Nombre
        if user_id == "Sistema" or "Empresa" in str(user_id):
            user_display = "Sistema"
            is_system = True
        else:
            try: 
                uid_int = int(user_id)
            except: 
                uid_int = user_id
            user_display = self.user_id_to_name.get(uid_int, f"Usuario {user_id}")
            is_system = False

        # Widget contenedor
        bubble_widget = QWidget()
        bubble_layout = QHBoxLayout(bubble_widget)
        bubble_layout.setContentsMargins(10, 5, 10, 5)

        # Estilo REAL según usuario
        if is_system:
            style = """
                QWidget {
                    background: #fff9c4;
                    border-radius: 16px;
                    padding: 12px 18px;
                    border: 1px solid #ffd54f;
                    max-width: 500px;
                }
            """
            alignment = "center"
        else:
            if alignment == "right":
                radius = "18px 18px 4px 18px"
            else:
                radius = "18px 18px 18px 4px"

            style = f"""
                QWidget {{
                    background: {bubble_color};
                    border-radius: {radius};
                    padding: 12px 16px;
                    border: 1px solid #c8c8c8;
                    max-width: 500px;
                }}
            """

        bubble = QWidget()
        bubble.setStyleSheet(style)
        inner = QVBoxLayout(bubble)
        inner.setSpacing(4)

        # Header
        if not is_system:
            header = QHBoxLayout()
            user_label = QLabel(f"<b>{user_display}</b>")
            user_label.setStyleSheet("color: #1b4d6b; font-size: 12px")

            time_label = QLabel(self.format_timestamp(timestamp))
            time_label.setStyleSheet("color: #666; font-size: 10px")

            header.addWidget(user_label)
            header.addStretch()
            header.addWidget(time_label)
            inner.addLayout(header)

        # Texto mensaje
        t = QLabel(text)
        t.setWordWrap(True)
        t.setStyleSheet("color: #222; font-size: 14px;")
        t.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(t)

        # Alineación física en el layout
        if alignment == "center":
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()
        elif alignment == "left":
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()
        else:  # right
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)

        self.conversation_layout.addWidget(bubble_widget)

    def load_chat_selector(self):
        """Carga la lista de chats en el selector"""
        self.chat_selector.clear()
        resultados = self.results.get('resultados_detallados', {})
        for archivo in resultados.keys():
            chat_name = resultados[archivo]['graph_info']['metadata'].get('chat_name', archivo)
            if not chat_name or chat_name == 'Chat':
                chat_name = archivo.replace('.json', '').replace('_', ' ')
            self.chat_selector.addItem(f"💬 {chat_name}", archivo)
        
        if self.chat_selector.count() > 0:
            self.on_chat_selected(0)

    def on_chat_selected(self, index):
        if index >= 0:
            self.current_chat_index = index
            self.current_thread_index = 0
            self.load_chat_threads()

    def load_chat_threads(self):
        """Carga los hilos del chat seleccionado"""
        archivo = self.chat_selector.currentData()
        if not archivo or archivo not in self.chat_data:
            self.thread_info.setText("No hay hilos disponibles")
            return
            
        chat_info = self.chat_data[archivo]
        self.threads = chat_info.get('threads', {})
        self.total_threads = len(self.threads)

        if self.total_threads > 0:
            self.load_thread(self.current_thread_index)
        else:
            self.thread_info.setText("No se encontraron hilos")
            self.clear_conversation()

    def clear_conversation(self):
        """Limpia la conversación actual"""
        for i in reversed(range(self.conversation_layout.count())):
            item = self.conversation_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

    def format_timestamp(self, timestamp):
        """Formatea el timestamp para mostrar"""
        try:
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime("%H:%M • %d/%m")
            return timestamp
        except:
            return timestamp

    def scroll_to_bottom(self):
        """Desplaza al final de la conversación"""
        scrollbar = self.conversation_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def previous_thread(self):
        """Navega al hilo anterior"""
        if self.current_thread_index > 0:
            self.current_thread_index -= 1
            self.load_thread(self.current_thread_index)

    def next_thread(self):
        """Navega al siguiente hilo"""
        if self.current_thread_index < self.total_threads - 1:
            self.current_thread_index += 1
            self.load_thread(self.current_thread_index)

    def create_grafo_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("<h3 style='color: #2C6E91;'>🕸️ Visualización de Grafos</h3>")
        layout.addWidget(title)
        
        # Selector de chat para grafos
        graph_selector_layout = QHBoxLayout()
        graph_selector_layout.addWidget(QLabel("<b>Seleccionar Chat:</b>"))
        
        self.graph_selector = QComboBox()
        self.graph_selector.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #2C6E91;
                border-radius: 8px;
                min-width: 250px;
                font-size: 14px;
            }
        """)
        graph_selector_layout.addWidget(self.graph_selector)
        graph_selector_layout.addStretch()
        
        layout.addLayout(graph_selector_layout)
        
        # Pestañas para diferentes vistas del grafo
        graph_tabs = QTabWidget()
        
        # Vista visual del grafo
        visual_tab = self.create_visual_graph_tab()
        # Vista textual del grafo
        textual_tab = self.create_textual_graph_tab()
        
        graph_tabs.addTab(visual_tab, "🎨 Vista Visual Reducida")
        graph_tabs.addTab(textual_tab, "📝 Vista Textual Completa")
        
        layout.addWidget(graph_tabs)
        
        # Cargar selector de grafos
        self.load_graph_selector()
        self.graph_selector.currentIndexChanged.connect(self.on_graph_selected)
        
        return widget

    def create_visual_graph_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Información del grafo reducido
        info_label = QLabel("🔍 <b>Vista Reducida:</b> Máximo 12 nodos (mínimo 2 usuarios) mostrando relaciones principales")
        info_label.setStyleSheet("background: #e3f2fd; padding: 10px; border-radius: 8px; color: #1565c0;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Controles de zoom
        controls_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("➕ Zoom In")
        zoom_out_btn = QPushButton("➖ Zoom Out")
        reset_btn = QPushButton("🔄 Reset")
        
        for btn in [zoom_in_btn, zoom_out_btn, reset_btn]:
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background: #6c757d;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #5a6268;
                }
            """)
        
        controls_layout.addWidget(zoom_in_btn)
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(reset_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Gráfico del grafo
        self.graph_view = GraphVisualization(None)
        layout.addWidget(self.graph_view)
        
        # Conectar botones de zoom
        zoom_in_btn.clicked.connect(lambda: self.graph_view.scale(1.2, 1.2))
        zoom_out_btn.clicked.connect(lambda: self.graph_view.scale(0.8, 0.8))
        reset_btn.clicked.connect(lambda: self.graph_view.reset_view())
        
        # Leyenda mejorada
        legend = QWidget()
        legend_layout = QVBoxLayout(legend)
        
        # Primera fila de leyenda
        legend_row1 = QHBoxLayout()
        legend_items = [
            ("🔵", "Usuarios (displayname)", "#2C6E91"),
            ("🟢", "Mensajes (💬+ID)", "#28a745"), 
            ("🔗", "Conexiones (con peso)", "#2C6E91")
        ]
        
        for icon, text, color in legend_items:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            
            icon_label = QLabel(icon)
            text_label = QLabel(text)
            text_label.setStyleSheet(f"color: {color}; font-weight: bold; margin-left: 5px; font-size: 12px;")
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(text_label)
            legend_row1.addWidget(item_widget)
            legend_row1.addSpacing(20)
        
        # Segunda fila de instrucciones
        legend_row2 = QHBoxLayout()
        instructions = QLabel("💡 <b>Interactúa:</b> Haz hover sobre mensajes para ver texto completo • Usa rueda del mouse para zoom • Arrastra para mover")
        instructions.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        legend_row2.addWidget(instructions)
        
        legend_layout.addLayout(legend_row1)
        legend_layout.addLayout(legend_row2)
        
        layout.addWidget(legend)
        
        return widget

    def create_textual_graph_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Información del grafo completo
        info_label = QLabel("📊 <b>Vista Textual Completa:</b> Hasta 100 nodos (mínimo 10 usuarios) mostrando estructura completa")
        info_label.setStyleSheet("background: #f3e5f5; padding: 10px; border-radius: 8px; color: #7b1fa2;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Información del grafo seleccionado
        self.graph_info_label = QLabel()
        self.graph_info_label.setWordWrap(True)
        content_layout.addWidget(self.graph_info_label)
        
        # Representación textual del grafo
        self.graph_text_representation = QTextEdit()
        self.graph_text_representation.setReadOnly(True)
        self.graph_text_representation.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        content_layout.addWidget(self.graph_text_representation)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget

    def on_graph_selected(self, index):
        """Cuando se selecciona un chat para visualizar el grafo"""
        if index >= 0:
            archivo = self.graph_selector.currentData()
            
            if archivo not in self.chat_data:
                return
                
            chat_info = self.chat_data[archivo]
            graph_data = chat_info.get('graph_data', {})
            
            # Actualizar vista visual con grafo reducido
            self.graph_view.graph_data = graph_data
            self.graph_view.draw_reduced_graph()
            
            # Actualizar vista textual con grafo enriquecido
            self.update_textual_graph_info(chat_info)

    def update_textual_graph_info(self, chat_info):
        """Actualiza la información textual del grafo con hasta 100 nodos y mínimo 10 usuarios"""
        graph_data = chat_info.get('graph_data', {})
        analysis_data = chat_info.get('analysis_data', {})
        
        if not graph_data:
            self.graph_info_label.setText("<div style='background: white; padding: 20px; border-radius: 10px;'><h4>No hay datos del grafo disponibles</h4></div>")
            self.graph_text_representation.setPlainText("No hay datos del grafo disponibles.")
            return
        
        # Información general
        chat_name = graph_data.get('metadata', {}).get('metadata', {}).get('chat_name', 'Chat Desconocido')
        
        nodes = graph_data.get('nodes', {})
        edges = graph_data.get('edges', [])
        
        user_nodes_count = len([n for n in nodes.values() if n.get('node_type') == 'user'])
        message_nodes_count = len([n for n in nodes.values() if n.get('node_type') == 'message'])
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        info_text = f"""
        <div style='background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px;'>
            <h4 style='color: #2C6E91;'>📊 Estadísticas del Grafo - {chat_name}</h4>
            
            <div style='display: flex; justify-content: space-between;'>
                <div style='flex: 1;'>
                    <h5>🏗️ Estructura Completa</h5>
                    <p>• <b>Nodos totales:</b> {total_nodes}</p>
                    <p>• <b>Usuarios:</b> {user_nodes_count}</p>
                    <p>• <b>Mensajes:</b> {message_nodes_count}</p>
                    <p>• <b>Conexiones:</b> {total_edges}</p>
                </div>
                
                <div style='flex: 1;'>
                    <h5>💬 Análisis de Conversación</h5>
                    <p>• <b>Hilos reconstruidos:</b> {analysis_data.get('thread_metrics', {}).get('total_threads', 0)}</p>
                    <p>• <b>Longitud promedio:</b> {analysis_data.get('thread_metrics', {}).get('avg_thread_length', 0):.1f} mensajes</p>
                    <p>• <b>Usuarios activos:</b> {len(analysis_data.get('user_engagement', {}).get('user_engagement_score', {}))}</p>
                    <p>• <b>Patrones detectados:</b> {len(analysis_data.get('conversation_patterns', {}).get('common_intention_patterns', []))}</p>
                </div>
            </div>
        </div>
        """
        
        self.graph_info_label.setText(info_text)
        
        # Representación textual enriquecida del grafo
        graph_text = self.generate_enriched_graph_text(graph_data)
        self.graph_text_representation.setPlainText(graph_text)

    def generate_enriched_graph_text(self, graph_data):
        """Genera una representación textual enriquecida con hasta 100 nodos y mínimo 10 usuarios"""
        
        nodes = graph_data.get('nodes', {})
        edges = graph_data.get('edges', [])
        
        if not nodes:
            return "No hay datos del grafo disponibles."
        
        selected_nodes = self.select_nodes_for_enriched_view(nodes, edges)
        
        text = "REPRESENTACIÓN TEXTUAL ENRIQUECIDA DEL GRAFO\n"
        text += "=" * 60 + "\n\n"
        
        text += "👥 USUARIOS PARTICIPANTES (Top 10+):\n"
        text += "-" * 40 + "\n"
        
        user_nodes = {
            nid: ndata for nid, ndata in nodes.items()
            if ndata.get('node_type') == 'user' and nid in selected_nodes
        }

        # Contar actividad por usuario
        user_activity = {}
        for edge in edges:
            if edge.get('source') in user_nodes:
                user_activity[edge['source']] = user_activity.get(edge['source'], 0) + 1
        
        sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
        
        for i, (user_id, activity) in enumerate(sorted_users[:15]):
            user_data = user_nodes.get(user_id, {})
            name = user_data.get('name') or "Sin nombre"
            username = user_data.get('username') or "desconocido"
            
            clean_user_id = user_id.replace("user_", "")
            try:
                user_id_int = int(clean_user_id)
                display_name = self.user_id_to_name.get(user_id_int) or name
            except Exception:
                display_name = name
            
            display_name = str(display_name)
            username = str(username)
            
            display_name = display_name[:30]
            username = username[:15]
            
            text += (
                f"{i+1:2d}. {display_name:30} "
                f"(@{username:15}) | Actividad: {activity} conexiones\n"
            )
        
        if len(user_nodes) > 15:
            text += f"... y {len(user_nodes) - 15} usuarios más\n"
        
        text += "\n" + "=" * 60 + "\n\n"

        text += "💬 ESTRUCTURA DE CONVERSACIONES:\n"
        text += "-" * 40 + "\n\n"
        
        message_nodes = {
            nid: ndata for nid, ndata in nodes.items()
            if ndata.get('node_type') == 'message' and nid in selected_nodes
        }

        # Encontrar mensajes raíz (sin incoming)
        root_messages = []
        for msg_id in message_nodes:
            has_incoming = any(
                edge.get('target') == msg_id and edge.get('source') in message_nodes
                for edge in edges
            )
            if not has_incoming:
                root_messages.append(msg_id)
        
        conversation_count = 0
        for root_msg in root_messages[:10]:
            conversation_text = self.extract_conversation_thread(
                root_msg, message_nodes, edges, selected_nodes
            )
            if conversation_text:
                conversation_count += 1
                text += f"🧵 CONVERSACIÓN {conversation_count}:\n"
                text += conversation_text + "\n"
        
        text += "\n" + "=" * 60 + "\n\n"
        
        text += "📊 ESTADÍSTICAS DETALLADAS:\n"
        text += "-" * 40 + "\n"
        
        total_selected = len(selected_nodes)
        users_selected = len(user_nodes)
        messages_selected = len(message_nodes)
        
        text += f"• Nodos mostrados: {total_selected}/100 (límite)\n"
        text += f"• Usuarios mostrados: {users_selected}/10+ (mínimo)\n"
        text += f"• Mensajes mostrados: {messages_selected}\n"
        
        dens = len(edges) / max(len(nodes) * (len(nodes) - 1), 1)
        text += f"• Densidad de conexiones: {dens:.4f}\n"
        
        intention_count = {}
        for node in message_nodes.values():
            intention = node.get('intention') or "desconocido"
            intention_count[intention] = intention_count.get(intention, 0) + 1
        
        if intention_count:
            text += "• Distribución de intenciones:\n"
            for intent, count in intention_count.items():
                percentage = (count / messages_selected) * 100
                text += f"    - {intent}: {count} ({percentage:.1f}%)\n"
        
        return text

    def select_nodes_for_enriched_view(self, nodes, edges):
        """Selecciona hasta 100 nodos con mínimo 10 usuarios para la vista textual"""
        user_nodes = [nid for nid, ndata in nodes.items() if ndata.get('node_type') == 'user']
        message_nodes = [nid for nid, ndata in nodes.items() if ndata.get('node_type') == 'message']
        
        # Seleccionar mínimo 10 usuarios (o todos si hay menos)
        selected_users = user_nodes[:max(10, min(20, len(user_nodes)))]
        
        # Seleccionar mensajes que sean de los usuarios seleccionados
        user_ids_selected = [uid.replace('user_', '') for uid in selected_users]
        selected_messages = []
        
        # Primero buscar mensajes enviados por los usuarios seleccionados
        for edge in edges:
            source = edge['source']
            target = edge['target']
            
            if (source in selected_users and 
                target in message_nodes and 
                target not in selected_messages):
                selected_messages.append(target)
        
        # Si no hay suficientes mensajes, agregar los más conectados
        if len(selected_messages) < 90:
            message_scores = {}
            for edge in edges:
                source, target = edge['source'], edge['target']
                weight = edge.get('data', {}).get('weight', 1.0)
                
                if source in message_nodes:
                    message_scores[source] = message_scores.get(source, 0) + weight
                if target in message_nodes:
                    message_scores[target] = message_scores.get(target, 0) + weight
            
            available_slots = 100 - len(selected_users)
            sorted_messages = sorted(message_scores.items(), key=lambda x: x[1], reverse=True)
            additional_messages = [msg[0] for msg in sorted_messages[:available_slots] if msg[0] not in selected_messages]
            selected_messages.extend(additional_messages)
        
        selected_messages = selected_messages[:90]
        
        return set(selected_users + selected_messages)

    def create_sentiment_analysis_tab(self, summary):
        """Crea el tab de análisis de sentimientos"""
        # Widget principal del tab
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("<h2>Análisis de Sentimientos</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2C6E91; padding: 10px;")
        layout.addWidget(title)
        
        # Scroll area para contenido largo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Resumen general
        general_group = QGroupBox("📊 Resumen General")
        general_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #2C6E91;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2C6E91;
            }
        """)
        
        general_layout = QVBoxLayout()
        
        # Estadísticas principales
        stats_grid = QGridLayout()
        
        total_messages = summary.get('total_messages', 0)
        avg_score = summary.get('average_score', 0.0)
        most_common = summary.get('most_common_sentiment', 'N/A')
        
        stats_grid.addWidget(QLabel("<b>Total de Mensajes Analizados:</b>"), 0, 0)
        stats_grid.addWidget(QLabel(f"<span style='color: #2C6E91; font-size: 14px;'>{total_messages}</span>"), 0, 1)
        
        stats_grid.addWidget(QLabel("<b>Puntuación Promedio:</b>"), 1, 0)
        stats_grid.addWidget(QLabel(f"<span style='color: #2C6E91; font-size: 14px;'>{avg_score:.2f}</span>"), 1, 1)
        
        stats_grid.addWidget(QLabel("<b>Sentimiento Más Común:</b>"), 2, 0)
        
        # Color según sentimiento
        sentiment_color = {
            'positivo': '#4CAF50',
            'negativo': '#F44336', 
            'neutral': '#FF9800'
        }.get(most_common.lower(), '#2C6E91')
        
        stats_grid.addWidget(QLabel(f"<span style='color: {sentiment_color}; font-size: 14px; font-weight: bold;'>{most_common.capitalize()}</span>"), 2, 1)
        
        general_layout.addLayout(stats_grid)
        
        # Distribución y porcentajes
        distribution = summary.get('distribution', {})
        percentages = summary.get('percentages', {})
        
        if distribution:
            dist_text = "<h5>📈 Distribución de Sentimientos:</h5><ul>"
            for label, count in distribution.items():
                dist_text += f"<li><b>{label.capitalize()}:</b> {count} mensajes</li>"
            dist_text += "</ul>"
            
            perc_text = "<h5>📊 Porcentajes:</h5><ul>"
            for label, perc in percentages.items():
                # Barra de progreso visual
                bar_width = int(perc * 2)
                bar = "█" * (bar_width // 4) + "░" * (50 - bar_width // 4)
                perc_text += f"<li><b>{label.capitalize()}:</b> {perc}% {bar}</li>"
            perc_text += "</ul>"
            
            general_layout.addWidget(QLabel(dist_text))
            general_layout.addWidget(QLabel(perc_text))
        
        general_group.setLayout(general_layout)
        content_layout.addWidget(general_group)
        
        # Análisis por usuario
        user_sentiments = summary.get('user_sentiments', {})
        if user_sentiments:
            user_group = QGroupBox("👥 Análisis por Participante")
            user_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #2C6E91;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                    color: #2C6E91;
                }
            """)
            
            user_layout = QVBoxLayout()
            
            for idx, (user, data) in enumerate(user_sentiments.items()):
                user_frame = QFrame()
                user_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
                user_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {'#f8f9fa' if idx % 2 == 0 else '#ffffff'};
                        border-radius: 6px;
                        padding: 10px;
                        border: 1px solid #dee2e6;
                    }}
                """)
                
                user_inner_layout = QVBoxLayout(user_frame)
                
                # Nombre de usuario
                user_name = QLabel(f"<h4>👤 {user}</h4>")
                user_name.setStyleSheet("color: #2C6E91;")
                user_inner_layout.addWidget(user_name)
                
                # Estadísticas del usuario
                user_stats = QGridLayout()
                
                user_stats.addWidget(QLabel("<b>Mensajes:</b>"), 0, 0)
                user_stats.addWidget(QLabel(f"<span style='color: #495057;'>{data['total_messages']}</span>"), 0, 1)
                
                user_stats.addWidget(QLabel("<b>Puntuación Promedio:</b>"), 1, 0)
                user_stats.addWidget(QLabel(f"<span style='color: #495057;'>{data['average_score']:.2f}</span>"), 1, 1)
                
                user_most_common = data['most_common_sentiment']
                user_stats.addWidget(QLabel("<b>Sentimiento Más Común:</b>"), 2, 0)
                
                user_sentiment_color = {
                    'positivo': '#4CAF50',
                    'negativo': '#F44336',
                    'neutral': '#FF9800'
                }.get(user_most_common.lower(), '#495057')
                
                user_stats.addWidget(QLabel(f"<span style='color: {user_sentiment_color}; font-weight: bold;'>{user_most_common.capitalize()}</span>"), 2, 1)
                
                user_inner_layout.addLayout(user_stats)
                
                # Distribución del usuario
                user_dist_text = "<b>Distribución:</b><br>"
                for label, count in data['distribution'].items():
                    user_dist_text += f"  • {label.capitalize()}: {count}<br>"
                
                user_perc_text = "<b>Porcentajes:</b><br>"
                for label, perc in data['percentages'].items():
                    user_perc_text += f"  • {label.capitalize()}: {perc}%<br>"
                
                user_inner_layout.addWidget(QLabel(user_dist_text))
                user_inner_layout.addWidget(QLabel(user_perc_text))
                
                user_layout.addWidget(user_frame)
            
            user_group.setLayout(user_layout)
            content_layout.addWidget(user_group)
        
        # Añadir widget de contenido al scroll
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return tab_widget

    def extract_conversation_thread(self, root_msg, message_nodes, edges, selected_nodes):
        """Extrae un hilo de conversación a partir de un mensaje raíz"""
        thread = []
        visited = set()
        
        def traverse_message(msg_id, depth=0):
            if msg_id in visited or msg_id not in selected_nodes:
                return
                
            visited.add(msg_id)
            msg_data = message_nodes.get(msg_id, {})
            text = msg_data.get('text', '')
            intention = msg_data.get('intention', 'desconocido')
            
            short_text = text[:80] + "..." if len(text) > 80 else text
            indent = "  " * depth
            thread.append(f"{indent}└─ {intention.upper()}: {short_text} [ID: {msg_id[-6:]}]")
            
            replies = [edge['target'] for edge in edges 
                      if edge['source'] == msg_id and edge['target'] in message_nodes]
            
            for reply in replies:
                traverse_message(reply, depth + 1)
        
        traverse_message(root_msg)
        return "\n".join(thread) if thread else ""

    def load_graph_selector(self):
        """Carga los chats en el selector de grafos"""
        self.graph_selector.clear()
        resultados = self.results.get('resultados_detallados', {})
        for archivo in resultados.keys():
            chat_name = resultados[archivo]['graph_info']['metadata'].get('chat_name', archivo)
            if not chat_name or chat_name == 'Chat':
                chat_name = archivo.replace('.json', '').replace('_', ' ')
            self.graph_selector.addItem(f"💬 {chat_name}", archivo)

    def load_chat_data(self):
        """Carga todos los datos de los chats procesados"""
        chat_data = {}
        
        for archivo in self.results.get('resultados_detallados', {}).keys():
            base_name = os.path.splitext(archivo)[0]
            threads_file = f"threads_analysis_results/{base_name}_threads.json"
            graph_file = f"threads_analysis_results/{base_name}_graph.json"
            analysis_file = f"threads_analysis_results/{base_name}_analysis.json"
            patterns_file = f"threads_analysis_results/{base_name}_patterns.json"  
            trends_file = f"threads_analysis_results/{base_name}_trends.json"  
            
            # Cargar datos de hilos
            if os.path.exists(threads_file):
                try:
                    with open(threads_file, 'r', encoding='utf-8') as f:
                        chat_data[archivo] = json.load(f)
                    
                    # Cargar información de usuarios desde el grafo
                    if os.path.exists(graph_file):
                        with open(graph_file, 'r', encoding='utf-8') as f:
                            graph_data = json.load(f)
                            nodes = graph_data.get('nodes', {})
                            
                            chat_data[archivo]['graph_data'] = graph_data
                            
                            for node_id, node_info in nodes.items():
                                if node_info.get('node_type') == 'user':
                                    user_id = node_id.replace('user_', '')
                                    try:
                                        user_id_int = int(user_id)
                                    except ValueError:
                                        user_id_int = user_id
                                    
                                    name = node_info.get('name', '')
                                    username = node_info.get('username', '')
                                    
                                    if name and username:
                                        display_name = f"{name} @{username}"
                                    elif name:
                                        display_name = name
                                    elif username:
                                        display_name = f"@{username}"
                                    else:
                                        display_name = f"Usuario {user_id}"
                                    
                                    if user_id_int not in self.user_id_to_name:
                                        self.user_id_to_name[user_id_int] = display_name
                    
                    # Cargar datos de análisis avanzado
                    if os.path.exists(analysis_file):
                        with open(analysis_file, 'r', encoding='utf-8') as f:
                            analysis_data = json.load(f)
                            chat_data[archivo]['analysis_data'] = analysis_data
                    else:
                        chat_data[archivo]['analysis_data'] = {}
                    
                    # NUEVO: Cargar datos de patrones
                    if os.path.exists(patterns_file):
                        with open(patterns_file, 'r', encoding='utf-8') as f:
                            patterns_data = json.load(f)
                            chat_data[archivo]['patterns_data'] = patterns_data
                    else:
                        chat_data[archivo]['patterns_data'] = {}
                    
                    # NUEVO: Cargar datos de tendencias
                    if os.path.exists(trends_file):
                        with open(trends_file, 'r', encoding='utf-8') as f:
                            trends_data = json.load(f)
                            chat_data[archivo]['trends_data'] = trends_data
                    else:
                        chat_data[archivo]['trends_data'] = {}
                                                
                except Exception as e:
                    print(f"Error cargando {threads_file}: {e}")
            else:
                print(f"Archivo no encontrado: {threads_file}")
        
        return chat_data

    def create_analisis_tab(self):
        """Crea la pestaña de análisis con buscador y secciones mejoradas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # NUEVO: Barra de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Buscar Chat:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escribe el nombre del chat...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #2C6E91;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_analysis_cards)
        
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
        title = QLabel("<h3 style='color: #2C6E91;'>📈 Análisis Detallado</h3>")
        layout.addWidget(title)
        
        self.analysis_scroll = QScrollArea()
        self.analysis_scroll.setWidgetResizable(True)
        
        self.analysis_content = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_content)
        self.analysis_layout.setSpacing(15)
        
        # Crear todas las tarjetas de análisis
        self.analysis_cards = []
        for archivo in self.chat_data.keys():
            resultados_detallados = self.results.get('resultados_detallados', {})
            datos_resultados = resultados_detallados.get(archivo, {})
            datos_chat = self.chat_data.get(archivo, {})
            
            datos_combinados = {
                'graph_info': datos_resultados.get('graph_info', {}),
                'analysis_summary': datos_resultados.get('analysis_summary', {}),
                'analysis_data': datos_chat.get('analysis_data', {}),
                'graph_data': datos_chat.get('graph_data', {}),
                'patterns_data': datos_chat.get('patterns_data', {}),  # NUEVO
                'trends_data': datos_chat.get('trends_data', {})      # NUEVO
            }
            
            analysis_card = self.create_detailed_analysis_card(archivo, datos_combinados)
            self.analysis_layout.addWidget(analysis_card)
            self.analysis_cards.append(analysis_card)
        
        self.analysis_layout.addStretch()
        self.analysis_scroll.setWidget(self.analysis_content)
        layout.addWidget(self.analysis_scroll)
        
        return widget

    def filter_analysis_cards(self, text):
        """Filtra las tarjetas de análisis basado en el texto de búsqueda"""
        for card in self.analysis_cards:
            chat_name = getattr(card, 'chat_name', '').lower()
            if text.lower() in chat_name:
                card.show()
            else:
                card.hide()

    def create_detailed_analysis_card(self, archivo, datos):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(card)
        
        # Guardar nombre del chat para el filtrado
        chat_name = datos.get('graph_info', {}).get('metadata', {}).get('chat_name', archivo)
        if not chat_name or chat_name == 'Chat':
            chat_name = archivo.replace('.json', '').replace('_', ' ')
        card.chat_name = chat_name
        
        # Header
        header = QWidget()
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2C6E91, stop:1 #6f42c1); border-top-left-radius: 10px; border-top-right-radius: 10px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title = QLabel(f"📊 {chat_name}")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        
        # Botón para ir al chat
        go_to_chat_btn = QPushButton("💬 Ir al Chat")
        go_to_chat_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid white;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        go_to_chat_btn.clicked.connect(lambda: self.go_to_chat(archivo))
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(go_to_chat_btn)
        
        # Tabs para diferentes tipos de análisis
        tabs = QTabWidget()
        
        # Pestaña de Resumen (existente)
        resumen_tab = self.create_resumen_analysis_tab(datos)
        tabs.addTab(resumen_tab, "📊 Resumen")
        
        # NUEVO: Pestaña de Patrones
        patrones_tab = self.create_patrones_tab(datos.get('patterns_data', {}))
        tabs.addTab(patrones_tab, "🔍 Patrones")
        
        # NUEVO: Pestaña de Tendencias
        tendencias_tab = self.create_tendencias_tab(datos.get('trends_data', {}))
        tabs.addTab(tendencias_tab, "📈 Tendencias")
        
        layout.addWidget(header)
        layout.addWidget(tabs)
        
        return card

    def go_to_chat(self, archivo):
        """Navega al chat específico en la pestaña de hilos"""
        # Buscar el índice del chat en el selector
        for i in range(self.chat_selector.count()):
            if self.chat_selector.itemData(i) == archivo:
                self.chat_selector.setCurrentIndex(i)
                self.tab_widget.setCurrentIndex(1)  # Ir a pestaña de hilos
                break

    def create_resumen_analysis_tab(self, datos):
        """Crea la pestaña de resumen existente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Obtener todos los datos
        analisis = datos.get('analysis_summary', {})
        graph_info = datos.get('graph_info', {})
        analysis_data = datos.get('analysis_data', {})
        graph_data = datos.get('graph_data', {})
        
        # Extraer métricas
        thread_metrics = analysis_data.get('thread_metrics', {})
        content_analysis = analysis_data.get('content_analysis', {})
        temporal_analysis = analysis_data.get('temporal_analysis', {})
        user_engagement = analysis_data.get('user_engagement', {})
        
        # Obtener distribución de intenciones
        intention_dist = content_analysis.get('intention_distribution', {})
        
        # Obtener distribución temporal
        threads_by_time = temporal_analysis.get('threads_by_time_of_day', {})
        if not threads_by_time:
            threads_by_time = self.calculate_time_distribution(analysis_data)
        
        # Calcular métricas del grafo
        total_nodes = graph_info.get('total_nodos', 0)
        nodes = graph_data.get('nodes', {})
        
        user_nodes_count = 0
        message_nodes_count = 0
        
        if nodes and isinstance(nodes, dict):
            for node_id, node_info in nodes.items():
                if isinstance(node_info, dict):
                    node_type = node_info.get('node_type')
                    if node_type == 'user':
                        user_nodes_count += 1
                    elif node_type == 'message':
                        message_nodes_count += 1
        
        total_edges = graph_info.get('total_aristas', 0)
        density = total_edges / max(total_nodes * (total_nodes - 1), 1) if total_nodes > 1 else 0
        
        # Obtener métricas de engagement de usuarios
        user_engagement_score = user_engagement.get('user_engagement_score', {})
        most_active_users = user_engagement.get('most_active_users', [])
        total_unique_users = len(user_engagement_score)
        top_user_messages = most_active_users[0][1] if most_active_users else 0
        
        # Tres columnas de métricas
        metrics_layout = QHBoxLayout()
        
        # Columna 1: Métricas de conversación
        col1 = QVBoxLayout()
        col1_title = QLabel("<b>💬 Conversación</b>")
        col1_title.setStyleSheet("color: #2C6E91; font-size: 14px; margin-bottom: 10px;")
        col1.addWidget(col1_title)
        
        metrics1 = [
            ("🧵 Total de Hilos", f"{thread_metrics.get('total_threads', 0)}"),
            ("📏 Long. Promedio Hilos", f"{thread_metrics.get('avg_thread_length', 0):.1f} msgs"),
            ("📈 Hilo Más Largo", f"{thread_metrics.get('max_thread_length', 0)} msgs"),
            ("📉 Hilo Más Corto", f"{thread_metrics.get('min_thread_length', 0)} msgs"),
            ("📊 Total Mensajes", f"{content_analysis.get('total_messages_analyzed', 0)}"),
            ("👤 Usuarios Únicos", f"{total_unique_users}"),
        ]
        
        for label, value in metrics1:
            metric_row = QHBoxLayout()
            metric_label = QLabel(label)
            metric_label.setStyleSheet("color: #495057;")
            value_label = QLabel(f"<b>{value}</b>")
            value_label.setStyleSheet("color: #2C6E91; font-size: 13px;")
            
            metric_row.addWidget(metric_label)
            metric_row.addStretch()
            metric_row.addWidget(value_label)
            col1.addLayout(metric_row)
        
        col1.addStretch()
        
        # Columna 2: Métricas del grafo
        col2 = QVBoxLayout()
        col2_title = QLabel("<b>🕸️ Estructura del Grafo</b>")
        col2_title.setStyleSheet("color: #2C6E91; font-size: 14px; margin-bottom: 10px;")
        col2.addWidget(col2_title)
        
        metrics2 = [
            ("🔵 Nodos Totales", f"{total_nodes}"),
            ("👤 Nodos Usuario", f"{user_nodes_count}"),
            ("💬 Nodos Mensaje", f"{message_nodes_count}"),
            ("🔗 Conexiones", f"{total_edges}"),
            ("📊 Densidad", f"{density:.4f}"),
            ("🏗️ Tipo de Grafo", "Dirigido"),
        ]
        
        for label, value in metrics2:
            metric_row = QHBoxLayout()
            metric_label = QLabel(label)
            metric_label.setStyleSheet("color: #495057;")
            value_label = QLabel(f"<b>{value}</b>")
            value_label.setStyleSheet("color: #2C6E91; font-size: 13px;")
            
            metric_row.addWidget(metric_label)
            metric_row.addStretch()
            metric_row.addWidget(value_label)
            col2.addLayout(metric_row)
        
        col2.addStretch()
        
        # Columna 3: Análisis avanzado completo
        col3 = QVBoxLayout()
        col3_title = QLabel("<b>📈 Análisis Avanzado</b>")
        col3_title.setStyleSheet("color: #2C6E91; font-size: 14px; margin-bottom: 10px;")
        col3.addWidget(col3_title)
        
        metrics3 = [
            ("📝 Long. Prom. Mensaje", f"{content_analysis.get('avg_message_length', 0):.1f} chars"),
            ("❓ Preguntas", f"{intention_dist.get('question', 0)}"),
            ("💬 Declaraciones", f"{intention_dist.get('statement', 0)}"),
            ("🛍️ Ofertas", f"{intention_dist.get('offer', 0)}"),
            ("👋 Saludos", f"{intention_dist.get('greeting', 0)}"),
            ("ℹ️ Informaciones", f"{intention_dist.get('information', 0)}"),
            ("🌅 Mañana", f"{threads_by_time.get('morning', 0)}"),
            ("🌇 Tarde", f"{threads_by_time.get('afternoon', 0)}"),
            ("🌃 Noche", f"{threads_by_time.get('night', 0)}"),
            ("🌟 Usuario Top", f"{top_user_messages} msgs"),
        ]
        
        for label, value in metrics3:
            metric_row = QHBoxLayout()
            metric_label = QLabel(label)
            metric_label.setStyleSheet("color: #495057;")
            value_label = QLabel(f"<b>{value}</b>")
            value_label.setStyleSheet("color: #2C6E91; font-size: 13px;")
            
            metric_row.addWidget(metric_label)
            metric_row.addStretch()
            metric_row.addWidget(value_label)
            col3.addLayout(metric_row)
        
        col3.addStretch()
        
        metrics_layout.addLayout(col1)
        metrics_layout.addSpacing(20)
        metrics_layout.addLayout(col2)
        metrics_layout.addSpacing(20)
        metrics_layout.addLayout(col3)
        
        layout.addLayout(metrics_layout)
        
        # INFORMACIÓN ADICIONAL MEJORADA
        additional_info = QWidget()
        additional_layout = QVBoxLayout(additional_info)
        
        # 1. GRÁFICO DE DISTRIBUCIÓN DE INTENCIONES
        if intention_dist:
            intention_widget = self.create_intention_distribution_widget(intention_dist)
            additional_layout.addWidget(intention_widget)
        
        # 2. GRÁFICO DE PATRONES COMUNES
        conversation_patterns = analysis_data.get('conversation_patterns', {})
        common_patterns = conversation_patterns.get('common_intention_patterns', [])
        if common_patterns:
            patterns_widget = self.create_patterns_widget(common_patterns)
            additional_layout.addWidget(patterns_widget)
        
        # 3. RANKING DE USUARIOS MÁS ACTIVOS
        if most_active_users:
            users_widget = self.create_top_users_widget(most_active_users)
            additional_layout.addWidget(users_widget)
        
        layout.addWidget(additional_info)
        
        return widget

    def create_patrones_tab(self, patterns_data):
        """Crea la pestaña de patrones detectados con mejor presentación"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if not patterns_data:
            no_data_label = QLabel(
                "🔍 No se detectaron patrones significativos en este chat\n\n"
                "Los patrones incluyen información sobre:\n"
                "• 💰 Referencias financieras y precios\n"
                "• 🕐 Fechas y tiempos mencionados\n"
                "• 👥 Interacciones sociales y menciones\n"
                "• 📞 Información de contacto\n"
                "• 🔧 Elementos técnicos"
            )
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("""
                color: #6c757d; 
                font-size: 14px; 
                padding: 40px;
                background: #f8f9fa;
                border-radius: 10px;
                line-height: 1.6;
            """)
            layout.addWidget(no_data_label)
            return widget
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # METADATOS MEJORADOS - MEJOR CONTRASTE
        metadata = patterns_data.get('metadata', {})
        if metadata:
            metadata_card = QFrame()
            metadata_card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3c72, stop:1 #2a5298);
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
            meta_layout = QGridLayout(metadata_card)
            
            title = QLabel("📊 Resumen del Análisis")
            title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            meta_layout.addWidget(title, 0, 0, 1, 2)
            
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Fecha de análisis:</b>"), 1, 0)
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{metadata.get('generated_at', 'N/A').replace('T', ' ').split('.')[0]}</span>"), 1, 1)
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Total mensajes:</b>"), 2, 0)
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{metadata.get('total_messages', 0)}</span>"), 2, 1)
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Versión:</b>"), 3, 0)
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{metadata.get('analysis_version', 'N/A')}</span>"), 3, 1)
            
            content_layout.addWidget(metadata_card)
        
        # PATRONES EXTRACTADOS - PRESENTACIÓN MEJORADA
        extracted_patterns = patterns_data.get('extracted_patterns', {})
        
        # 1. PATRONES TEMPORALES MEJORADOS (con contexto)
        temporal = extracted_patterns.get('temporal', {})
        if temporal and temporal.get('total_temporal_references', 0) > 0:
            temporal_card = self.create_temporal_patterns_card(temporal)
            content_layout.addWidget(temporal_card)
        
        # 2. PATRONES SOCIALES MEJORADOS
        social = extracted_patterns.get('social', {})
        if social and (social.get('social_engagement_score', 0) > 0 or 
                    social.get('mentions') or social.get('emojis') or social.get('hashtags') or social.get('urls')):
            social_card = self.create_social_patterns_card(social)
            content_layout.addWidget(social_card)
        
        # 3. PATRONES FINANCIEROS MEJORADOS
        financial = extracted_patterns.get('financial', {})
        if financial and (financial.get('total_monetary_references', 0) > 0 or 
                        financial.get('explicit_currencies') or financial.get('implicit_prices')):
            financial_card = self.create_financial_patterns_card(financial)
            content_layout.addWidget(financial_card)
        
        # 4. PATRONES DE CONTACTO
        contact = extracted_patterns.get('contact', {})
        if contact and contact.get('total_contact_points', 0) > 0:
            contact_card = self.create_contact_patterns_card(contact)
            content_layout.addWidget(contact_card)
        
        # 5. PATRONES TÉCNICOS
        technical = extracted_patterns.get('technical', {})
        if technical and technical.get('total_technical_patterns', 0) > 0:
            technical_card = self.create_technical_patterns_card(technical)
            content_layout.addWidget(technical_card)
        
        # ANÁLISIS DE MENSAJES (si existe)
        message_analysis = patterns_data.get('message_analysis', [])
        if message_analysis and len(message_analysis) > 0:
            messages_card = self.create_message_analysis_card(message_analysis)
            content_layout.addWidget(messages_card)
        
        # Si no hay patrones significativos
        if (not temporal.get('total_temporal_references', 0) and 
            not social.get('social_engagement_score', 0) and
            not financial.get('total_monetary_references', 0) and
            not contact.get('total_contact_points', 0) and
            not technical.get('total_technical_patterns', 0)):
            
            no_patterns_label = QLabel(
                "✅ No se detectaron patrones significativos en este chat\n\n"
                "Esto puede indicar:\n"
                "• Conversaciones informales o casuales\n"
                "• Contenido predominantemente textual simple\n"
                "• Ausencia de datos estructurados específicos"
            )
            no_patterns_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_patterns_label.setStyleSheet("""
                color: #28a745; 
                font-size: 14px; 
                padding: 30px;
                background: #f8fff9;
                border: 2px solid #28a745;
                border-radius: 10px;
                line-height: 1.6;
            """)
            content_layout.addWidget(no_patterns_label)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget

    def create_temporal_patterns_card(self, temporal_data):
        """Crea una tarjeta especial para patrones temporales con contexto mejorado"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #6f42c1;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("🕐 Referencias Temporales con Contexto")
        header.setStyleSheet("""
            background: #6f42c1;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Estadísticas generales
        total_refs = temporal_data.get('total_temporal_references', 0)
        stats_label = QLabel(f"📊 Se encontraron {total_refs} referencias temporales en total")
        stats_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
        content_layout.addWidget(stats_label)
        
        # Patrones con contexto (nueva estructura)
        patterns_with_context = temporal_data.get('patterns_with_context', {})
        
        if patterns_with_context:
            # Ordenar patrones por frecuencia
            sorted_patterns = sorted(
                patterns_with_context.items(),
                key=lambda x: x[1].get('total_count', 0),
                reverse=True
            )
            
            # Mostrar TODOS los patrones, no solo 10
            for pattern_key, pattern_data in sorted_patterns:
                pattern_widget = self.create_temporal_pattern_widget(pattern_key, pattern_data)
                content_layout.addWidget(pattern_widget)
                
                # Separador entre patrones
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: #e9ecef; margin: 10px 0px;")
                content_layout.addWidget(separator)
        
        # Mostrar también la estructura antigua para compatibilidad
        absolute_dates = temporal_data.get('absolute_dates', [])
        relative_refs = temporal_data.get('relative_references', [])
        time_expr = temporal_data.get('time_expressions', [])
        
        if absolute_dates or relative_refs or time_expr:
            legacy_section = QWidget()
            legacy_layout = QVBoxLayout(legacy_section)
            
            legacy_title = QLabel("📋 Resumen por Categorías (estructura anterior)")
            legacy_title.setStyleSheet("font-weight: bold; color: #6c757d; font-size: 14px; margin-top: 15px;")
            legacy_layout.addWidget(legacy_title)
            
            if absolute_dates:
                legacy_layout.addWidget(QLabel(f"• 📅 Fechas absolutas: {len(absolute_dates)}"))
            if relative_refs:
                legacy_layout.addWidget(QLabel(f"• ⏰ Referencias relativas: {len(relative_refs)}"))
            if time_expr:
                legacy_layout.addWidget(QLabel(f"• 🕒 Expresiones de tiempo: {len(time_expr)}"))
            
            content_layout.addWidget(legacy_section)
        
        layout.addWidget(content)
        return card

    def create_temporal_pattern_widget(self, pattern_key, pattern_data):
        """Crea un widget para mostrar un patrón temporal específico con su contexto - MEJORADO"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # Header del patrón
        header_layout = QHBoxLayout()
        
        pattern_text = pattern_data.get('pattern', pattern_key)
        total_count = pattern_data.get('total_count', 0)
        category = pattern_data.get('category', 'desconocida')
        
        # Emoji según el tipo de patrón - MÁS ESPECÍFICO
        emoji = "🕐"
        pattern_lower = pattern_text.lower()
        if 'hoy' in pattern_lower:
            emoji = "🌞"
        elif 'mañana' in pattern_lower or 'manana' in pattern_lower:
            emoji = "🌅"
        elif 'ayer' in pattern_lower:
            emoji = "🌙"
        elif 'semana' in pattern_lower:
            emoji = "📅"
        elif 'mes' in pattern_lower:
            emoji = "🗓️"
        elif 'año' in pattern_lower or 'ano' in pattern_lower:
            emoji = "📆"
        elif 'lunes' in pattern_lower or 'martes' in pattern_lower or 'miércoles' in pattern_lower or 'miercoles' in pattern_lower or 'jueves' in pattern_lower or 'viernes' in pattern_lower or 'sábado' in pattern_lower or 'sabado' in pattern_lower or 'domingo' in pattern_lower:
            emoji = "📅"
        elif 'enero' in pattern_lower or 'febrero' in pattern_lower or 'marzo' in pattern_lower or 'abril' in pattern_lower or 'mayo' in pattern_lower or 'junio' in pattern_lower or 'julio' in pattern_lower or 'agosto' in pattern_lower or 'septiembre' in pattern_lower or 'octubre' in pattern_lower or 'noviembre' in pattern_lower or 'diciembre' in pattern_lower:
            emoji = "🗓️"
        
        pattern_label = QLabel(f"{emoji} \"{pattern_text}\"")
        pattern_label.setStyleSheet("font-weight: bold; color: #6f42c1; font-size: 14px;")
        
        count_label = QLabel(f"{total_count} veces")
        count_label.setStyleSheet("background: #6f42c1; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;")
        
        category_label = QLabel(f"Categoría: {category.replace('dates_', '').replace('_', ' ')}")
        category_label.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic;")
        
        header_layout.addWidget(pattern_label)
        header_layout.addWidget(count_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        layout.addWidget(category_label)
        
        # Contextos de ejemplo - MOSTRAR TODOS, no solo 3
        example_contexts = pattern_data.get('example_contexts', [])
        occurrences = pattern_data.get('occurrences', [])
        
        if example_contexts:
            contexts_label = QLabel("💬 Contextos de ejemplo:")
            contexts_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px; margin-top: 5px;")
            layout.addWidget(contexts_label)
            
            # Mostrar TODOS los contextos, no solo 3
            for i, context in enumerate(example_contexts):
                context_widget = QWidget()
                context_layout = QHBoxLayout(context_widget)
                
                # Número
                num_label = QLabel(f"{i+1}.")
                num_label.setStyleSheet("color: #6c757d; font-weight: bold; min-width: 20px;")
                
                # Contexto
                context_text = QLabel(context)
                context_text.setStyleSheet("color: #495057; font-size: 12px;")
                context_text.setWordWrap(True)
                
                context_layout.addWidget(num_label)
                context_layout.addWidget(context_text)
                context_layout.addStretch()
                
                layout.addWidget(context_widget)
        
        # Información de usuarios
        users = pattern_data.get('users', set())
        if users:
            users_label = QLabel(f"👥 Mencionado por {len(users)} usuario(s)")
            users_label.setStyleSheet("color: #6c757d; font-size: 11px; margin-top: 5px;")
            layout.addWidget(users_label)
        
        return widget

    def create_message_analysis_card(self, message_analysis):
        """Crea una tarjeta para el análisis de mensajes individuales"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #17a2b8;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("💬 Análisis de Mensajes Destacados")
        header.setStyleSheet("""
            background: #17a2b8;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        # Contenido con scroll
        scroll_content = QScrollArea()
        scroll_content.setWidgetResizable(True)
        scroll_content.setFixedHeight(300)
        scroll_content.setStyleSheet("border: none; background: #f8f9fa;")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        # Mostrar máximo 10 mensajes destacados
        for i, msg in enumerate(message_analysis[:10]):
            msg_widget = self.create_message_pattern_widget(msg, i+1)
            scroll_layout.addWidget(msg_widget)
        
        scroll_layout.addStretch()
        scroll_content.setWidget(scroll_widget)
        layout.addWidget(scroll_content)
        
        return card

    def create_message_pattern_widget(self, msg_data, index):
        """Crea un widget para mostrar análisis de mensaje individual"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        layout = QVBoxLayout(widget)
        
        # Header del mensaje
        header_layout = QHBoxLayout()
        
        # Número e información básica
        number_label = QLabel(f"{index}.")
        number_label.setStyleSheet("font-weight: bold; color: #2C6E91; min-width: 25px;")
        
        timestamp = msg_data.get('timestamp', '')
        if 'T' in timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M • %d/%m")
            except:
                time_str = timestamp
        else:
            time_str = timestamp
        
        time_label = QLabel(f"🕐 {time_str}")
        time_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        # Contar patrones detectados
        patterns = msg_data.get('patterns_detected', {})
        pattern_count = sum(1 for v in patterns.values() if v) if patterns else 0
        
        patterns_label = QLabel(f"🔍 {pattern_count} patrones")
        patterns_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        header_layout.addWidget(number_label)
        header_layout.addWidget(time_label)
        header_layout.addStretch()
        header_layout.addWidget(patterns_label)
        
        # Texto del mensaje
        text = msg_data.get('enriched_text', msg_data.get('text', 'Sin texto'))
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #495057; font-size: 13px; margin: 5px 0;")
        text_label.setWordWrap(True)
        
        # Patrones específicos encontrados (solo mostrar los que tienen datos)
        if patterns and pattern_count > 0:
            patterns_found = []
            pattern_categories = {
                'dates_relative_simple': '🕐 Fechas',
                'mentions': '👤 Menciones', 
                'emojis': '😊 Emojis',
                'dates_absolute': '📅 Fechas absolutas',
                'precios_implicitos': '💰 Precios'
            }
            
            for pattern_key, pattern_label in pattern_categories.items():
                if patterns.get(pattern_key):
                    patterns_found.append(pattern_label)
            
            if patterns_found:
                patterns_text = " | ".join(patterns_found)
                patterns_info = QLabel(f"📊 Detectado: {patterns_text}")
                patterns_info.setStyleSheet("color: #28a745; font-size: 11px; font-weight: bold;")
                layout.addWidget(patterns_info)
        
        layout.addLayout(header_layout)
        layout.addWidget(text_label)
        
        return widget

    def create_social_patterns_card(self, social_data):
        """Crea una tarjeta para patrones sociales con información MEJORADA"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e83e8c;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("👥 Interacciones Sociales")
        header.setStyleSheet("""
            background: #e83e8c;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Puntuación de compromiso MEJORADA - en español con explicación
        engagement_score = social_data.get('social_engagement_score', 0)
        engagement_label = QLabel(f"📊 Puntuación de Compromiso: {engagement_score}")
        engagement_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
        content_layout.addWidget(engagement_label)
        
        # Explicación de la puntuación
        explanation = QLabel(
            "💡 Esta puntuación mide el nivel de interacción social en el chat. "
            "Se calcula basándose en menciones, emojis, hashtags y URLs encontradas. "
            "Una puntuación más alta indica mayor actividad social."
        )
        explanation.setStyleSheet("color: #6c757d; font-size: 12px; background: #f8f9fa; padding: 10px; border-radius: 8px;")
        explanation.setWordWrap(True)
        content_layout.addWidget(explanation)
        
        # Menciones - MOSTRAR TODAS
        mentions = social_data.get('mentions', [])
        if mentions:
            mentions_section = QWidget()
            mentions_layout = QVBoxLayout(mentions_section)
            
            mentions_label = QLabel(f"👤 Menciones encontradas: {len(mentions)}")
            mentions_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px;")
            mentions_layout.addWidget(mentions_label)
            
            # Scroll area para menciones
            mentions_scroll = QScrollArea()
            mentions_scroll.setFixedHeight(120)
            mentions_scroll.setWidgetResizable(True)
            mentions_scroll.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 5px; background: #f8f9fa;")
            
            mentions_content = QWidget()
            mentions_content_layout = QVBoxLayout(mentions_content)
            
            for mention in mentions:
                mention_label = QLabel(f"• {mention}")
                mention_label.setStyleSheet("color: #495057; font-size: 12px; padding: 2px 0;")
                mentions_content_layout.addWidget(mention_label)
            
            mentions_scroll.setWidget(mentions_content)
            mentions_layout.addWidget(mentions_scroll)
            content_layout.addWidget(mentions_section)
        
        # Emojis - MOSTRAR TODOS con frecuencia
        emojis = social_data.get('emojis', [])
        if emojis:
            from collections import Counter
            emoji_counts = Counter(emojis)
            top_emojis = emoji_counts.most_common()
            
            emojis_section = QWidget()
            emojis_layout = QVBoxLayout(emojis_section)
            
            emojis_label = QLabel(f"😊 Emojis utilizados: {len(emojis)} total, {len(emoji_counts)} únicos")
            emojis_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px; margin-top: 10px;")
            emojis_layout.addWidget(emojis_label)
            
            # Mostrar emojis más usados
            emoji_grid = QWidget()
            emoji_grid_layout = QHBoxLayout(emoji_grid)
            emoji_grid_layout.setSpacing(10)
            
            for emoji, count in top_emojis[:15]:  # Mostrar top 15 emojis
                emoji_widget = QWidget()
                emoji_widget_layout = QVBoxLayout(emoji_widget)
                emoji_widget_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                emoji_label = QLabel(emoji)
                emoji_label.setStyleSheet("font-size: 20px;")
                
                count_label = QLabel(str(count))
                count_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: bold;")
                
                emoji_widget_layout.addWidget(emoji_label)
                emoji_widget_layout.addWidget(count_label)
                emoji_grid_layout.addWidget(emoji_widget)
            
            emoji_grid_layout.addStretch()
            emojis_layout.addWidget(emoji_grid)
            
            # Si hay más emojis, mostrar en lista
            if len(top_emojis) > 15:
                more_emojis_label = QLabel(f"... y {len(top_emojis) - 15} emojis más")
                more_emojis_label.setStyleSheet("color: #adb5bd; font-size: 11px; font-style: italic;")
                emojis_layout.addWidget(more_emojis_label)
            
            content_layout.addWidget(emojis_section)
        
        # Hashtags - MOSTRAR TODOS
        hashtags = social_data.get('hashtags', [])
        if hashtags:
            hashtags_label = QLabel(f"#️⃣ Hashtags encontrados: {len(hashtags)}")
            hashtags_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px; margin-top: 10px;")
            content_layout.addWidget(hashtags_label)
            
            hashtags_text = ", ".join(hashtags)
            hashtags_content = QLabel(hashtags_text)
            hashtags_content.setStyleSheet("color: #495057; font-size: 12px; background: #f8f9fa; padding: 8px; border-radius: 5px;")
            hashtags_content.setWordWrap(True)
            content_layout.addWidget(hashtags_content)
        
        # URLs - MOSTRAR TODAS
        urls = social_data.get('urls', [])
        if urls:
            urls_label = QLabel(f"🔗 URLs encontradas: {len(urls)}")
            urls_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px; margin-top: 10px;")
            content_layout.addWidget(urls_label)
            
            for url in urls:
                url_label = QLabel(f"• {url}")
                url_label.setStyleSheet("color: #495057; font-size: 11px; font-family: monospace;")
                url_label.setWordWrap(True)
                content_layout.addWidget(url_label)
        
        layout.addWidget(content)
        return card

    def create_financial_patterns_card(self, financial_data):
        """Crea una tarjeta para patrones financieros con información MEJORADA"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #28a745;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("💰 Referencias Financieras")
        header.setStyleSheet("""
            background: #28a745;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        total_refs = financial_data.get('total_monetary_references', 0)
        if total_refs > 0:
            total_label = QLabel(f"📊 Total de referencias financieras: {total_refs}")
            total_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
            content_layout.addWidget(total_label)
        
        # Monedas explícitas - INFORMACIÓN ÚTIL
        explicit_currencies = financial_data.get('explicit_currencies', [])
        if explicit_currencies:
            explicit_label = QLabel(f"💵 Monedas explícitas encontradas: {len(explicit_currencies)}")
            explicit_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px;")
            content_layout.addWidget(explicit_label)
            
            for currency in explicit_currencies:
                if isinstance(currency, (list, tuple)) and len(currency) >= 2:
                    amount, curr = currency[0], currency[1]
                    currency_label = QLabel(f"• {amount} {curr}")
                else:
                    currency_label = QLabel(f"• {currency}")
                currency_label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
                content_layout.addWidget(currency_label)
        
        # Precios implícitos - INFORMACIÓN ÚTIL
        implicit_prices = financial_data.get('implicit_prices', [])
        if implicit_prices:
            implicit_label = QLabel(f"💲 Precios implícitos mencionados: {len(implicit_prices)}")
            implicit_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px; margin-top: 10px;")
            content_layout.addWidget(implicit_label)
            
            for price in implicit_prices:
                price_label = QLabel(f"• {price}")
                price_label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
                content_layout.addWidget(price_label)
        
        # Distribución por moneda - INFORMACIÓN ÚTIL
        currency_breakdown = financial_data.get('currency_breakdown', {})
        if currency_breakdown:
            breakdown_label = QLabel("📈 Distribución por tipo de moneda:")
            breakdown_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 13px; margin-top: 10px;")
            content_layout.addWidget(breakdown_label)
            
            for currency, count in currency_breakdown.items():
                breakdown_item = QLabel(f"• {currency.upper()}: {count} referencias")
                breakdown_item.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
                content_layout.addWidget(breakdown_item)
        
        # Si no hay datos específicos pero hay referencias totales
        if total_refs > 0 and not explicit_currencies and not implicit_prices and not currency_breakdown:
            info_label = QLabel(
                "💡 Se detectaron referencias financieras en el chat, pero no se pudieron extraer detalles específicos. "
                "Esto puede deberse a formatos no estándar o menciones indirectas de precios."
            )
            info_label.setStyleSheet("color: #6c757d; font-size: 12px; background: #f8f9fa; padding: 10px; border-radius: 8px;")
            info_label.setWordWrap(True)
            content_layout.addWidget(info_label)
        
        layout.addWidget(content)
        return card

    def create_contact_patterns_card(self, contact_data):
        """Crea una tarjeta para patrones de contacto"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #fd7e14;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("📞 Información de Contacto")
        header.setStyleSheet("""
            background: #fd7e14;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        total_points = contact_data.get('total_contact_points', 0)
        total_label = QLabel(f"📊 Total de puntos de contacto: {total_points}")
        total_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
        content_layout.addWidget(total_label)
        
        # Mostrar toda la información disponible
        for key, value in contact_data.items():
            if key != 'total_contact_points' and value:
                key_label = QLabel(f"• {key.replace('_', ' ').title()}: {len(value) if isinstance(value, list) else value}")
                key_label.setStyleSheet("color: #495057; font-size: 12px;")
                content_layout.addWidget(key_label)
        
        layout.addWidget(content)
        return card

    def create_technical_patterns_card(self, technical_data):
        """Crea una tarjeta para patrones técnicos"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #6c757d;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        layout = QVBoxLayout(card)
        
        header = QLabel("🔧 Elementos Técnicos")
        header.setStyleSheet("""
            background: #6c757d;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px 15px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin: 0px;
        """)
        layout.addWidget(header)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        total_patterns = technical_data.get('total_technical_patterns', 0)
        total_label = QLabel(f"📊 Total de patrones técnicos: {total_patterns}")
        total_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
        content_layout.addWidget(total_label)
        
        # Mostrar toda la información disponible
        for key, value in technical_data.items():
            if key != 'total_technical_patterns' and value:
                key_label = QLabel(f"• {key.replace('_', ' ').title()}: {len(value) if isinstance(value, list) else value}")
                key_label.setStyleSheet("color: #495057; font-size: 12px;")
                content_layout.addWidget(key_label)
        
        layout.addWidget(content)
        return card

    def create_tendencias_tab(self, trends_data):
        """Crea la pestaña de tendencias con análisis mejorado"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if not trends_data:
            no_data_label = QLabel(
                "📈 No hay datos de tendencias disponibles para este chat\n\n"
                "El análisis de tendencias incluye:\n"
                "• 📊 Patrones de actividad por hora y día\n"
                "• 🔍 Comportamientos inusuales\n"
                "• 💰 Evolución de precios (si aplica)\n"
                "• 📋 Resumen ejecutivo y recomendaciones"
            )
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("""
                color: #6c757d; 
                font-size: 14px; 
                padding: 40px;
                background: #f8f9fa;
                border-radius: 10px;
                line-height: 1.6;
            """)
            layout.addWidget(no_data_label)
            return widget
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # METADATOS - MEJOR CONTRASTE
        metadata = trends_data.get('metadata', {})
        if metadata:
            meta_card = QFrame()
            meta_card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3c72, stop:1 #2a5298);
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
            meta_layout = QGridLayout(meta_card)
            
            title = QLabel("📈 Metadatos del Análisis")
            title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            meta_layout.addWidget(title, 0, 0, 1, 2)
            
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Generado:</b>"), 1, 0)
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{metadata.get('generated_at', 'N/A').replace('T', ' ').split('.')[0]}</span>"), 1, 1)
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Mensajes analizados:</b>"), 2, 0)
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{metadata.get('total_messages_analyzed', 0)}</span>"), 2, 1)
            meta_layout.addWidget(QLabel("<b style='color: #e0e0e0;'>Archivo fuente:</b>"), 3, 0)
            source = metadata.get('source_file', 'N/A')
            source_short = source.split('\\')[-1] if '\\' in source else source
            meta_layout.addWidget(QLabel(f"<span style='color: white;'>{source_short}</span>"), 3, 1)
            
            content_layout.addWidget(meta_card)
        
        # RESUMEN EJECUTIVO (lo más importante)
        executive_summary = trends_data.get('executive_summary', {})
        if executive_summary:
            summary_card = QFrame()
            summary_card.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 2px solid #28a745;
                    border-radius: 12px;
                    padding: 0px;
                }
            """)
            summary_layout = QVBoxLayout(summary_card)
            
            header = QLabel("🎯 Resumen Ejecutivo")
            header.setStyleSheet("""
                background: #28a745;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 15px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin: 0px;
            """)
            summary_layout.addWidget(header)
            
            content_widget = QWidget()
            content_inner = QVBoxLayout(content_widget)
            content_inner.setSpacing(12)
            content_inner.setContentsMargins(15, 15, 15, 15)
            
            # Hallazgos clave
            key_findings = executive_summary.get('key_findings', [])
            if key_findings:
                findings_label = QLabel("🔍 Hallazgos Clave:")
                findings_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px;")
                content_inner.addWidget(findings_label)
                
                for finding in key_findings:
                    finding_widget = QLabel(f"• {finding}")
                    finding_widget.setStyleSheet("color: #495057; margin-left: 10px;")
                    finding_widget.setWordWrap(True)
                    content_inner.addWidget(finding_widget)
            
            # Recomendaciones
            recommendations = executive_summary.get('recommendations', [])
            if recommendations:
                rec_label = QLabel("💡 Recomendaciones:")
                rec_label.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 14px; margin-top: 10px;")
                content_inner.addWidget(rec_label)
                
                for rec in recommendations:
                    rec_widget = QLabel(f"• {rec}")
                    rec_widget.setStyleSheet("color: #495057; margin-left: 10px;")
                    rec_widget.setWordWrap(True)
                    content_inner.addWidget(rec_widget)
            
            # Factores de riesgo
            risk_factors = executive_summary.get('risk_factors', [])
            if risk_factors:
                risk_label = QLabel("⚠️ Factores de Riesgo:")
                risk_label.setStyleSheet("font-weight: bold; color: #dc3545; font-size: 14px; margin-top: 10px;")
                content_inner.addWidget(risk_label)
                
                for risk in risk_factors:
                    risk_widget = QLabel(f"• {risk}")
                    risk_widget.setStyleSheet("color: #495057; margin-left: 10px;")
                    risk_widget.setWordWrap(True)
                    content_inner.addWidget(risk_widget)
            
            summary_layout.addWidget(content_widget)
            content_layout.addWidget(summary_card)
        
        # PATRONES TEMPORALES 
        temporal_patterns = trends_data.get('temporal_patterns', {})
        if temporal_patterns:
            temporal_card = QFrame()
            temporal_card.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 2px solid #6f42c1;
                    border-radius: 12px;
                    padding: 0px;
                }
            """)
            temp_layout = QVBoxLayout(temporal_card)
            
            header = QLabel("🕐 Patrones de Actividad Temporal")
            header.setStyleSheet("""
                background: #6f42c1;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 15px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin: 0px;
            """)
            temp_layout.addWidget(header)
            
            content_widget = QWidget()
            content_inner = QVBoxLayout(content_widget)
            content_inner.setSpacing(15)
            content_inner.setContentsMargins(15, 15, 15, 15)
            
            # Horas pico
            # Horas pico
            peak_hours = temporal_patterns.get('peak_hours', [])
            if peak_hours:
                peaks_label = QLabel("⏰ Horas de Mayor Actividad:")
                peaks_label.setStyleSheet("font-weight: bold; color: #2C6E91;")
                content_inner.addWidget(peaks_label)
                
                for i, peak in enumerate(peak_hours[:5]):  # Top 5 horas pico
                    hour = peak.get('hour', 0)
                    activity = peak.get('activity', 0)
                    
                    display_hour = hour % 12 or 12
                    period = "AM" if hour < 12 else "PM"
                    
                    peak_widget = QWidget()
                    peak_layout = QHBoxLayout(peak_widget)
                    
                    time_label = QLabel(f"{display_hour}:00 {period}")
                    time_label.setStyleSheet("font-weight: bold; color: #6f42c1; min-width: 70px;")
                    
                    # Barra de progreso visual
                    progress_container = QWidget()
                    progress_layout = QHBoxLayout(progress_container)
                    progress_layout.setContentsMargins(0, 0, 0, 0)
                    
                    max_activity = max([p.get('activity', 0) for p in peak_hours]) if peak_hours else 1
                    bar_width = int((activity / max_activity) * 150)
                    
                    progress_bar = QWidget()
                    progress_bar.setFixedHeight(15)
                    progress_bar.setFixedWidth(bar_width)
                    progress_bar.setStyleSheet("background: #6f42c1; border-radius: 7px;")
                    
                    count_label = QLabel(f"{activity} mensajes")
                    count_label.setStyleSheet("color: #6c757d; font-size: 12px; min-width: 80px;")
                    
                    progress_layout.addWidget(progress_bar)
                    progress_layout.addWidget(count_label)
                    progress_layout.addStretch()
                    
                    peak_layout.addWidget(time_label)
                    peak_layout.addWidget(progress_container)
                    content_inner.addWidget(peak_widget)
            
            # Actividad por hora del día  
            hourly_activity = temporal_patterns.get('hourly_activity', {})

            hourly_label = QLabel("📊 Distribución por Hora del Día:")
            hourly_label.setStyleSheet("font-weight: bold; color: #2C6E91; margin-top: 10px;")
            content_inner.addWidget(hourly_label)

            if not hourly_activity:
                no_data_label = QLabel("No hay datos de actividad por hora.")
                no_data_label.setStyleSheet("color: #6c757d; font-style: italic; margin-left: 10px;")
                content_inner.addWidget(no_data_label)
            else:
                # Crear un área de scroll para todas las horas
                hourly_scroll = QScrollArea()
                hourly_scroll.setFixedHeight(300)
                hourly_scroll.setWidgetResizable(True)
                hourly_scroll.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 5px; background: #f8f9fa;")
                
                hourly_content = QWidget()
                hourly_content_layout = QVBoxLayout(hourly_content)
                hourly_content_layout.setSpacing(5)
                
                # Convertir claves a int y ordenar de 0 a 23
                sorted_hours = sorted(int(h) for h in hourly_activity.keys())
                max_hourly_activity = max(hourly_activity.values()) if hourly_activity else 1
                
                for hour in sorted_hours:
                    activity = hourly_activity.get(str(hour), 0)
                    if activity > 0:
                        hour_widget = QWidget()
                        hour_layout = QHBoxLayout(hour_widget)
                        
                        # Formato AM/PM
                        display_hour = hour % 12 or 12
                        period = "AM" if hour < 12 else "PM"
                        hour_label = QLabel(f"{display_hour}:00 {period}")
                        hour_label.setStyleSheet("font-weight: bold; min-width: 80px; color: #495057;")
                        
                        # Barra de progreso
                        progress_container = QWidget()
                        progress_layout = QHBoxLayout(progress_container)
                        progress_layout.setContentsMargins(0, 0, 0, 0)
                        
                        bar_width = int((activity / max_hourly_activity) * 200)
                        progress_bar = QWidget()
                        progress_bar.setFixedHeight(12)
                        progress_bar.setFixedWidth(bar_width)
                        progress_bar.setStyleSheet("background: #6f42c1; border-radius: 6px;")
                        
                        count_label = QLabel(f"{activity} mensajes")
                        count_label.setStyleSheet("color: #6c757d; font-size: 11px; min-width: 80px;")
                        
                        progress_layout.addWidget(progress_bar)
                        progress_layout.addWidget(count_label)
                        progress_layout.addStretch()
                        
                        hour_layout.addWidget(hour_label)
                        hour_layout.addWidget(progress_container)
                        hour_layout.addStretch()
                        
                        hourly_content_layout.addWidget(hour_widget)
                
                hourly_scroll.setWidget(hourly_content)
                content_inner.addWidget(hourly_scroll)

            # Actividad por día de la semana
            daily_activity = temporal_patterns.get('daily_activity', {})
            if daily_activity:
                daily_label = QLabel("📅 Actividad por Día de la Semana:")
                daily_label.setStyleSheet("font-weight: bold; color: #2C6E91; margin-top: 10px;")
                content_inner.addWidget(daily_label)
                
                days_translation = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes', 
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                
                # Ordenar días de la semana
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                max_daily = max(daily_activity.values()) if daily_activity else 1
                
                for eng_day in day_order:
                    if eng_day in daily_activity:
                        esp_day = days_translation.get(eng_day, eng_day)
                        count = daily_activity[eng_day]
                        
                        day_widget = QWidget()
                        day_layout = QHBoxLayout(day_widget)
                        
                        day_label = QLabel(esp_day)
                        day_label.setStyleSheet("min-width: 80px; font-weight: bold;")
                        
                        # Barra de progreso para días
                        progress_container = QWidget()
                        progress_layout = QHBoxLayout(progress_container)
                        progress_layout.setContentsMargins(0, 0, 0, 0)
                        
                        bar_width = int((count / max_daily) * 150)
                        progress_bar = QWidget()
                        progress_bar.setFixedHeight(12)
                        progress_bar.setFixedWidth(bar_width)
                        progress_bar.setStyleSheet("background: #6f42c1; border-radius: 6px;")
                        
                        count_label = QLabel(f"{count} mensajes")
                        count_label.setStyleSheet("color: #6c757d; font-size: 11px; min-width: 70px;")
                        
                        progress_layout.addWidget(progress_bar)
                        progress_layout.addWidget(count_label)
                        progress_layout.addStretch()
                        
                        day_layout.addWidget(day_label)
                        day_layout.addWidget(progress_container)
                        day_layout.addStretch()
                        
                        content_inner.addWidget(day_widget)
                
                temp_layout.addWidget(content_widget)
                content_layout.addWidget(temporal_card)
                
        # ANOMALÍAS
        anomalies = trends_data.get('anomalies', {})
        if anomalies:
            anomalies_card = QFrame()
            anomalies_card.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 2px solid #dc3545;
                    border-radius: 12px;
                    padding: 0px;
                }
            """)
            anom_layout = QVBoxLayout(anomalies_card)
            
            header = QLabel("⚠️ Comportamientos Inusuales Detectados")
            header.setStyleSheet("""
                background: #dc3545;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 15px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin: 0px;
            """)
            anom_layout.addWidget(header)
            
            content_widget = QWidget()
            content_inner = QVBoxLayout(content_widget)
            content_inner.setSpacing(10)
            content_inner.setContentsMargins(15, 15, 15, 15)
            
            # Actividad inusual
            unusual_activity = anomalies.get('unusual_activity', [])
            if unusual_activity:
                for activity in unusual_activity:
                    hour = activity.get('hour', 0)
                    reason = activity.get('reason', '')
                    
                    display_hour = hour % 12 or 12
                    period = "AM" if hour < 12 else "PM"
                    
                    activity_widget = QLabel(f"• Hora {display_hour}:00 {period} - {reason}")
                    activity_widget.setStyleSheet("color: #495057;")
                    activity_widget.setWordWrap(True)
                    content_inner.addWidget(activity_widget)

            
            # Patrones sospechosos
            suspicious_patterns = anomalies.get('suspicious_patterns', [])
            if suspicious_patterns:
                suspicious_label = QLabel(f"🔍 {len(suspicious_patterns)} mensajes con patrones sospechosos detectados")
                suspicious_label.setStyleSheet("color: #495057; font-weight: bold;")
                content_inner.addWidget(suspicious_label)
            
            # Si no hay anomalías específicas
            if not unusual_activity and not suspicious_patterns:
                normal_label = QLabel("✅ No se detectaron comportamientos inusuales significativos")
                normal_label.setStyleSheet("color: #28a745; font-style: italic; text-align: center; padding: 20px;")
                content_inner.addWidget(normal_label)
            
            anom_layout.addWidget(content_widget)
            content_layout.addWidget(anomalies_card)
        
        # PERIODO DE TIEMPO
        price_analysis = trends_data.get('price_analysis', {})
        if price_analysis:
            time_period = price_analysis.get('time_period', {})
            if time_period:
                period_card = QFrame()
                period_card.setStyleSheet("""
                    QFrame {
                        background: white;
                        border: 2px solid #fd7e14;
                        border-radius: 12px;
                        padding: 0px;
                    }
                """)
                period_layout = QVBoxLayout(period_card)
                
                header = QLabel("📅 Periodo Analizado")
                header.setStyleSheet("""
                    background: #fd7e14;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 12px 15px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    margin: 0px;
                """)
                period_layout.addWidget(header)
                
                content_widget = QWidget()
                content_inner = QVBoxLayout(content_widget)
                content_inner.setContentsMargins(15, 15, 15, 15)
                
                start = time_period.get('start', '').replace('T', ' ').split('+')[0]
                end = time_period.get('end', '').replace('T', ' ').split('+')[0]
                days = time_period.get('days', 0)
                
                content_inner.addWidget(QLabel(f"<b>Inicio:</b> {start}"))
                content_inner.addWidget(QLabel(f"<b>Fin:</b> {end}"))
                content_inner.addWidget(QLabel(f"<b>Días analizados:</b> {days}"))
                
                period_layout.addWidget(content_widget)
                content_layout.addWidget(period_card)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget

    def create_intention_distribution_widget(self, intention_dist):
        """Crea un widget bonito para la distribución de intenciones"""
        widget = QWidget()
        widget.setStyleSheet("background: #f8f9fa; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout(widget)
        
        title = QLabel("📊 Distribución de Intenciones")
        title.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Traducciones al español
        translations = {
            'question': '❓ Preguntas',
            'statement': '💬 Declaraciones', 
            'offer': '🛍️ Ofertas',
            'greeting': '👋 Saludos',
            'information': 'ℹ️ Informaciones',
            'request': '🙏 Solicitudes'
        }
        
        # Crear barras de progreso para cada intención
        total = sum(intention_dist.values())
        
        for intent_key, count in intention_dist.items():
            intent_name = translations.get(intent_key, intent_key)
            percentage = (count / total) * 100 if total > 0 else 0
            
            intent_widget = QWidget()
            intent_layout = QHBoxLayout(intent_widget)
            
            # Nombre de la intención
            name_label = QLabel(intent_name)
            name_label.setStyleSheet("font-weight: bold; min-width: 120px;")
            name_label.setFixedWidth(120)
            
            # Barra de progreso
            progress_container = QWidget()
            progress_layout = QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(0, 0, 0, 0)
            
            progress_bar = QWidget()
            progress_bar.setFixedHeight(20)
            progress_width = int(percentage * 2)
            progress_bar.setFixedWidth(min(progress_width, 200))
            progress_bar.setStyleSheet(f"background: #2C6E91; border-radius: 10px;")
            
            # Texto con count y porcentaje
            count_label = QLabel(f"{count} ({percentage:.1f}%)")
            count_label.setStyleSheet("color: #495057; font-size: 12px; min-width: 80px;")
            
            progress_layout.addWidget(progress_bar)
            progress_layout.addWidget(count_label)
            progress_layout.addStretch()
            
            intent_layout.addWidget(name_label)
            intent_layout.addWidget(progress_container)
            intent_layout.addStretch()
            
            layout.addWidget(intent_widget)
        
        return widget

    def create_patterns_widget(self, common_patterns):
        """Crea un widget bonito para los patrones comunes"""
        widget = QWidget()
        widget.setStyleSheet("background: #f8f9fa; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout(widget)
        
        title = QLabel("🔄 Patrones de Conversación Más Comunes")
        title.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Traducciones al español
        translations = {
            'statement': 'Declaración',
            'question': 'Pregunta',
            'information': 'Información',
            'greeting': 'Saludo',
            'offer': 'Oferta',
            'request': 'Solicitud'
        }
        
        # Mostrar top 5 patrones
        for i, (pattern, count) in enumerate(common_patterns[:5]):
            translated_pattern = pattern
            for eng, esp in translations.items():
                translated_pattern = translated_pattern.replace(eng, esp)
            translated_pattern = translated_pattern.replace('→', '→')
            
            pattern_widget = QWidget()
            pattern_layout = QHBoxLayout(pattern_widget)
            
            # Número de ranking
            rank_label = QLabel(f"{i+1}.")
            rank_label.setStyleSheet("font-weight: bold; color: #2C6E91; min-width: 30px;")
            
            # Patrón traducido
            pattern_label = QLabel(translated_pattern)
            pattern_label.setStyleSheet("color: #495057;")
            pattern_label.setWordWrap(True)
            
            # Contador
            count_label = QLabel(f"{count} veces")
            count_label.setStyleSheet("color: #6c757d; font-size: 12px; min-width: 60px;")
            
            pattern_layout.addWidget(rank_label)
            pattern_layout.addWidget(pattern_label)
            pattern_layout.addStretch()
            pattern_layout.addWidget(count_label)
            
            layout.addWidget(pattern_widget)
        
        return widget

    def create_top_users_widget(self, most_active_users):
        """Crea un widget bonito para el top de usuarios más activos"""
        widget = QWidget()
        widget.setStyleSheet("background: #f8f9fa; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout(widget)
        
        title = QLabel("🏆 Top 5 Usuarios Más Activos")
        title.setStyleSheet("font-weight: bold; color: #2C6E91; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Mostrar top 5 usuarios
        for i, (user_id, count) in enumerate(most_active_users[:5]):
            display_name = self.user_id_to_name.get(user_id, f"Usuario {user_id}")
            
            user_widget = QWidget()
            user_layout = QHBoxLayout(user_widget)
            
            # Número de ranking con emoji
            emojis = ["🥇", "🥈", "🥉", "№ 4", "№ 5"]
            rank_label = QLabel(emojis[i] if i < len(emojis) else f"{i+1}.")
            rank_label.setStyleSheet("font-size: 16px; min-width: 30px;")
            
            # Nombre del usuario
            name_label = QLabel(display_name)
            name_label.setStyleSheet("font-weight: bold; color: #495057;")
            
            # Barra de actividad
            activity_widget = QWidget()
            activity_layout = QHBoxLayout(activity_widget)
            activity_layout.setContentsMargins(0, 0, 0, 0)
            
            activity_bar = QWidget()
            activity_bar.setFixedHeight(15)
            max_count = most_active_users[0][1] if most_active_users else 1
            bar_width = int((count / max_count) * 150)
            activity_bar.setFixedWidth(bar_width)
            activity_bar.setStyleSheet(f"background: #28a745; border-radius: 7px;")
            
            # Contador de mensajes
            count_label = QLabel(f"{count} mensajes")
            count_label.setStyleSheet("color: #6c757d; font-size: 12px; min-width: 80px;")
            
            activity_layout.addWidget(activity_bar)
            activity_layout.addWidget(count_label)
            activity_layout.addStretch()
            
            user_layout.addWidget(rank_label)
            user_layout.addWidget(name_label)
            user_layout.addStretch()
            user_layout.addWidget(activity_widget)
            
            layout.addWidget(user_widget)
        
        return widget

    def calculate_time_distribution(self, analysis_data):
        """Calcula la distribución de hilos por tiempo del día basado en las fechas disponibles"""
        threads_by_time = {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}
        
        try:
            temporal_analysis = analysis_data.get('temporal_analysis', {})
            thread_start_times = temporal_analysis.get('thread_start_times', [])
            
            if not thread_start_times:
                return threads_by_time
            
            for start_time in thread_start_times:
                try:
                    if 'T' in start_time:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        hour = dt.hour
                        
                        if 6 <= hour < 12:
                            threads_by_time['morning'] += 1
                        elif 12 <= hour < 18:
                            threads_by_time['afternoon'] += 1
                        elif 18 <= hour < 24:
                            threads_by_time['evening'] += 1
                        else:
                            threads_by_time['night'] += 1
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error calculando distribución temporal: {e}")
        
        return threads_by_time


class GraphVisualization(QGraphicsView):
    def __init__(self, graph_data, parent=None):
        super().__init__(parent)
        self.graph_data = graph_data

        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setSceneRect(-50000, -50000, 100000, 100000)

        # Render
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet(
            "background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 10px;"
        )
        self.setMinimumSize(800, 600)

        # Navegación
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Zoom state
        self.initial_fit_done = False

        if graph_data:
            self.draw_reduced_graph()

    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in

        old_pos = self.mapToScene(event.position().toPoint())

        factor = zoom_in if event.angleDelta().y() > 0 else zoom_out

        self.scale(factor, factor)

        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def draw_reduced_graph(self):
        self.scene.clear()
        if not self.graph_data:
            return

        G = nx.DiGraph()
        nodes_data = self.graph_data.get("nodes", {})
        edges_data = self.graph_data.get("edges", [])

        selected_nodes = self.select_nodes_for_reduced_graph(nodes_data, edges_data)
        if not selected_nodes:
            return

        for n in selected_nodes:
            if n in nodes_data:
                G.add_node(n, **nodes_data[n])

        for e in edges_data:
            if e["source"] in selected_nodes and e["target"] in selected_nodes:
                G.add_edge(e["source"], e["target"], **e.get("data", {}))

        if not G.nodes():
            return

        # Layout
        try:
            pos = nx.spring_layout(G, k=150, iterations=80)
        except Exception:
            pos = nx.circular_layout(G)

        pos = {n: (p[0] * 800, p[1] * 800) for n, p in pos.items()}

        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        margin = 200
        scene_rect = QRectF(
            min_x - margin,
            min_y - margin,
            (max_x - min_x) + margin * 2,
            (max_y - min_y) + margin * 2,
        )

        self.scene.setSceneRect(scene_rect.adjusted(-2000, -2000, 2000, 2000))

        self._draw_edges(G, pos)
        self._draw_nodes(G, pos, nodes_data)

        if not self.initial_fit_done:
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(scene_rect.center())
            self.initial_fit_done = True
        
        self.graph_rect = scene_rect

    def reset_view(self):
        if hasattr(self, "graph_rect"):
            self.resetTransform()
            self.fitInView(self.graph_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(self.graph_rect.center())

    def _draw_edges(self, G, pos):
        for u, v, data in G.edges(data=True):
            x1, y1 = pos[u]
            x2, y2 = pos[v]

            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            line_item.setPen(QPen(Qt.GlobalColor.black, 2))
            self.scene.addItem(line_item)

            dx = x2 - x1
            dy = y2 - y1
            angle = math.atan2(dy, dx)

            arrow_size = 22
            tip_x = x2 - 10 * math.cos(angle)
            tip_y = y2 - 10 * math.sin(angle)

            p1 = QPointF(
                tip_x - arrow_size * math.cos(angle - math.pi / 6),
                tip_y - arrow_size * math.sin(angle - math.pi / 6),
            )
            p2 = QPointF(
                tip_x - arrow_size * math.cos(angle + math.pi / 6),
                tip_y - arrow_size * math.sin(angle + math.pi / 6),
            )
            p3 = QPointF(tip_x, tip_y)

            polygon = QPolygonF([p1, p2, p3])
            arrow_item = QGraphicsPolygonItem(polygon)
            arrow_item.setBrush(Qt.GlobalColor.black)
            arrow_item.setPen(QPen(Qt.GlobalColor.black))
            self.scene.addItem(arrow_item)

            w = data.get("weight", data.get("w", None))
            if w is not None:
                try:
                    w = round(float(w), 2)
                    edge_label = f"{w:.2f}"
                except Exception:
                    edge_label = str(w)
            else:
                edge_label = ""

            if edge_label:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                offset = 18
                perp_angle = angle + math.pi / 2
                mid_x += offset * math.cos(perp_angle)
                mid_y += offset * math.sin(perp_angle)

                text_item = QGraphicsTextItem(edge_label)
                text_item.setDefaultTextColor(Qt.GlobalColor.darkBlue)

                brect = text_item.boundingRect()
                text_item.setPos(mid_x - brect.width() / 2,
                                 mid_y - brect.height() / 2)

                self.scene.addItem(text_item)

    def _draw_nodes(self, G, pos, nodes_data):
        node_radius = 20
        for node_id, (x, y) in pos.items():
            node_info = nodes_data.get(node_id, {})
            node_type = node_info.get("node_type", "unknown")

            if node_type == "user":
                color = QColor("#2C6E91")
                parent = self.parent()
                while parent and not hasattr(parent, "user_id_to_name"):
                    parent = parent.parent()
                if parent and hasattr(parent, "user_id_to_name"):
                    user_id = node_id.replace("user_", "")
                    try:
                        uid = int(user_id)
                        display_name = parent.user_id_to_name.get(uid, "Usuario")
                    except Exception:
                        display_name = "Usuario"
                else:
                    display_name = node_info.get("name", "Usuario")
                label_text = (display_name[:3] if display_name else "Usr")
                tooltip = f"Usuario: {display_name}\nID: {node_id}"
            else:
                color = QColor("#28a745")
                message_text = node_info.get("text", "Mensaje")
                message_id = node_id.replace("msg_", "")
                tooltip = f"Mensaje completo:\n{message_text}\n\nID: {message_id}\nTipo: {node_info.get('intention','N/A')}"
                label_text = f"💬{message_id[:4]}..."

            ellipse = QGraphicsEllipseItem(-node_radius, -node_radius, 2 * node_radius, 2 * node_radius)
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(Qt.GlobalColor.white, 2))
            ellipse.setPos(x, y)
            ellipse.setToolTip(tooltip)
            ellipse.setData(0, node_id)
            self.scene.addItem(ellipse)

            text_item = QGraphicsTextItem(label_text)
            text_item.setDefaultTextColor(Qt.GlobalColor.white)
            text_item.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            tw = text_item.boundingRect().width()
            th = text_item.boundingRect().height()
            text_item.setPos(x - tw / 2, y - th / 2)
            self.scene.addItem(text_item)

    def select_nodes_for_reduced_graph(self, nodes_data, edges_data):
        user_nodes = []
        message_nodes = []
        for node_id, node_info in nodes_data.items():
            if node_info.get("node_type") == "user":
                user_nodes.append(node_id)
            elif node_info.get("node_type") == "message":
                message_nodes.append(node_id)

        selected_users = user_nodes[:max(2, min(4, len(user_nodes)))]

        selected_messages = []
        for edge in edges_data:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in selected_users and tgt in message_nodes and tgt not in selected_messages:
                selected_messages.append(tgt)

        if len(selected_messages) < 8:
            message_scores = {}
            for edge in edges_data:
                s, t = edge.get("source"), edge.get("target")
                w = edge.get("data", {}).get("weight", 1.0)
                if s in message_nodes:
                    message_scores[s] = message_scores.get(s, 0) + w
                if t in message_nodes:
                    message_scores[t] = message_scores.get(t, 0) + w
            sorted_msgs = sorted(message_scores.items(), key=lambda x: x[1], reverse=True)
            additional = [m for m, _ in sorted_msgs[:8] if m not in selected_messages]
            selected_messages.extend(additional)

        selected_messages = selected_messages[:8]
        all_selected = selected_users + selected_messages
        return all_selected[:12]