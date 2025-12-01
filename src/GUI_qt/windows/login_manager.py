import os
import json
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit
)
from GUI_qt.utils.config import get_config
from GUI_qt.utils.paths import paths
from GUI_qt.windows.login_dialog import LoginDialog
from core.config.user_credentials import has_credentials, get_credentials

current_dir = str(paths.gui_dir)
assets = os.path.join(current_dir, 'assets')


class LoginManagerWindow(QWidget):
    def __init__(self, providers):
        super().__init__()
        self.providers = [p for p in providers if getattr(p, 'has_login', False)]
        self._setup_ui()
        self._load_translations()
        self._populate_list()
    
    def _setup_ui(self):
        self.setWindowTitle("Gerenciar Logins")
        self.setWindowIcon(QIcon(os.path.join(assets, 'icon.ico')))
        self.resize(450, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titulo
        title = QLabel("Gerenciar Credenciais")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #bb86fc;")
        layout.addWidget(title)
        
        # Subtitulo
        subtitle = QLabel("Configure suas credenciais para sites que exigem login")
        subtitle.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Barra de busca
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar provider...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #424242;
                border-radius: 6px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #7e57c2;
            }
        """)
        self.search_bar.textChanged.connect(self._filter_providers)
        layout.addWidget(self.search_bar)
        
        # Lista de providers
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #424242;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                border-radius: 4px;
                padding: 10px;
                margin: 3px 0;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #7e57c2;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._open_login_dialog)
        layout.addWidget(self.list_widget)
        
        # Botoes
        button_layout = QHBoxLayout()
        
        self.config_btn = QPushButton("Configurar Login")
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #7e57c2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9575cd; }
            QPushButton:pressed { background-color: #673ab7; }
            QPushButton:disabled { background-color: #424242; color: #757575; }
        """)
        self.config_btn.clicked.connect(self._config_selected)
        button_layout.addWidget(self.config_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_translations(self):
        config = get_config()
        language = config.lang if config else QLocale.system().name()
        
        translations = {}
        try:
            with open(os.path.join(assets, 'translations.json'), 'r', encoding='utf-8') as file:
                translations = json.load(file)
        except:
            pass
        
        if language not in translations:
            language = 'en'
    
    def _populate_list(self):
        self.list_widget.clear()
        
        for provider in self.providers:
            domain = provider.domain[0] if isinstance(provider.domain[0], str) else str(provider.domain[0])
            has_creds = has_credentials(domain)
            
            status = "Configurado" if has_creds else "Nao configurado"
            status_color = "#4caf50" if has_creds else "#ff9800"
            
            item = QListWidgetItem()
            item.setText(f"{provider.name}")
            item.setData(Qt.ItemDataRole.UserRole, provider)
            
            # Criar widget customizado para o item
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            name_label = QLabel(provider.name)
            name_label.setStyleSheet("color: white; font-weight: bold;")
            layout.addWidget(name_label)
            
            layout.addStretch()
            
            status_label = QLabel(status)
            status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
            layout.addWidget(status_label)
            
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
    
    def _filter_providers(self):
        text = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            provider = item.data(Qt.ItemDataRole.UserRole)
            if text in provider.name.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _config_selected(self):
        current = self.list_widget.currentItem()
        if current:
            self._open_login_dialog(current)
    
    def _open_login_dialog(self, item):
        provider = item.data(Qt.ItemDataRole.UserRole)
        domain = provider.domain[0] if isinstance(provider.domain[0], str) else str(provider.domain[0])
        
        dialog = LoginDialog(provider.name, domain, self)
        if dialog.exec():
            # Refresh list
            self._populate_list()
