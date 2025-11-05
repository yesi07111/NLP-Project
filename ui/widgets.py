from PyQt6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt


class ChatListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_chats = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Barra superior con botón "Seleccionar Todo"
        top_bar = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Seleccionar Todo")
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C6E91;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A88B1;
            }
        """)
        self.select_all_btn.clicked.connect(self.toggle_select_all_chats)
        
        self.selected_count_label = QLabel("0 seleccionados")
        self.selected_count_label.setStyleSheet("color: #666; font-size: 11px;")
        
        top_bar.addWidget(self.select_all_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.selected_count_label)

        layout.addLayout(top_bar)

        # Lista de chats
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def toggle_select_all_chats(self):
        """Alterna entre seleccionar todos y deseleccionar todos"""
        total_chats = self.list_widget.count()
        if total_chats == 0:
            return
            
        # Verificar si ya están todos seleccionados
        all_selected = True
        for i in range(total_chats):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if not checkbox.isChecked():
                    all_selected = False
                    break
        
        # Alternar estado
        new_state = not all_selected
        
        for i in range(total_chats):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                checkbox.setChecked(new_state)
        
        # Actualizar texto del botón
        if new_state:
            self.select_all_btn.setText("Deseleccionar Todo")
        else:
            self.select_all_btn.setText("Seleccionar Todo")

    def update_selected_count(self):
        """Actualiza el contador de chats seleccionados"""
        selected_count = len(self.selected_chats)
        self.selected_count_label.setText(f"{selected_count} seleccionados")
        
        # Actualizar texto del botón basado en el estado actual
        total_chats = self.list_widget.count()
        if total_chats > 0 and selected_count == total_chats:
            self.select_all_btn.setText("Deseleccionar Todo")
        else:
            self.select_all_btn.setText("Seleccionar Todo")

    def add_chat_item(self, chat_info):
        def clip_name(name: str, max_len=30) -> str:
            return name if len(name) <= max_len else name[: max_len - 3] + "..."

        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(8)

        checkbox = QCheckBox()
        checkbox.stateChanged.connect(
            lambda state, chat=chat_info: self.toggle_chat_selection(chat, state)
        )
        layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignLeft)

        name: str = chat_info.get("name", "Sin nombre")
        if "deleted=True" in name:
            name = "Usuario eliminado"

        label = QLabel()
        label.setText(clip_name(name))
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        label.setWordWrap(False)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        label.setToolTip(name if len(name) > 30 else "")

        unread = chat_info.get("unread_count", 0)
        if unread > 0:
            label.setText(f"{clip_name(name)} ({unread})")
            label.setStyleSheet("font-weight: bold;")

        layout.addWidget(label, 1)

        preview_btn = QPushButton("👁️")
        preview_btn.setFixedSize(30, 25)
        preview_btn.setToolTip("Vista previa del chat")
        preview_btn.setStyleSheet(
            """
            QPushButton {
                background-color:#f0f0f0;
                border:1px solid #ccc;
                border-radius:3px;
            }
            QPushButton:hover {
                background-color:#e0e0e0;
            }
            """
        )
        preview_btn.clicked.connect(lambda _, c=chat_info: self.show_preview(c))

        layout.addWidget(preview_btn, 0, Qt.AlignmentFlag.AlignRight)

        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())

        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, item_widget)

    def show_preview(self, chat_info):
        parent = self.parent()
        while parent:
            if hasattr(parent, "preview_chat"):
                try:
                    parent.preview_chat(chat_info)
                    return
                except Exception as e:
                    print(f"Error llamando preview_chat en parent: {e}")
            if hasattr(parent, "show_chat_preview"):
                try:
                    parent.show_chat_preview(chat_info)
                    return
                except Exception as e:
                    print(f"Error llamando show_chat_preview en parent: {e}")
            parent = parent.parent() if parent.parent() else None

        QMessageBox.warning(self, "Error", "No se pudo abrir la vista previa del chat.")

    def toggle_chat_selection(self, chat_info, state):
        if state == Qt.CheckState.Checked.value:
            if chat_info not in self.selected_chats:
                self.selected_chats.append(chat_info)
        else:
            if chat_info in self.selected_chats:
                self.selected_chats.remove(chat_info)
        self.update_selected_count()

    def get_selected_chats(self):
        return self.selected_chats.copy()

    def clear_selection(self):
        self.selected_chats.clear()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                checkbox.setChecked(False)
        self.update_selected_count()

    def clear(self):
        self.list_widget.clear()
        self.selected_chats.clear()
        self.update_selected_count()