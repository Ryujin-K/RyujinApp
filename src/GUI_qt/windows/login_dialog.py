from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.config.user_credentials import save_credentials, get_credentials, delete_credentials


class LoginDialog(QDialog):
    def __init__(self, provider_name: str, provider_domain: str, parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.provider_domain = provider_domain
        self.credentials = None
        self._setup_ui()
        self._load_existing_credentials()
    
    def _setup_ui(self):
        self.setWindowTitle(f"Login - {self.provider_name}")
        self.setMinimumSize(450, 380)
        self.resize(450, 380)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 35, 40, 35)
        
        # Titulo
        title_label = QLabel(f"Login {self.provider_name}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #bb86fc; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Subtitulo
        subtitle = QLabel("Suas credenciais serao salvas localmente")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("seu@email.com")
        self.email_input.setMinimumHeight(42)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #424242;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #7e57c2;
            }
        """)
        layout.addWidget(self.email_input)
        
        layout.addSpacing(8)
        
        # Senha
        password_label = QLabel("Senha:")
        password_label.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Sua senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #424242;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #7e57c2;
            }
        """)
        layout.addWidget(self.password_input)
        
        # Mostrar senha
        self.show_password = QCheckBox("Mostrar senha")
        self.show_password.setStyleSheet("color: #888; font-size: 12px; margin-top: 5px;")
        self.show_password.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password)
        
        layout.addSpacing(15)
        
        # Botoes
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.delete_btn = QPushButton("Remover")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:pressed { background-color: #b71c1c; }
        """)
        self.delete_btn.clicked.connect(self._delete_credentials)
        self.delete_btn.hide()
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Salvar")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(100)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #7e57c2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #9575cd; }
            QPushButton:pressed { background-color: #673ab7; }
        """)
        save_btn.clicked.connect(self._save_credentials)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _load_existing_credentials(self):
        creds = get_credentials(self.provider_domain)
        if creds:
            self.email_input.setText(creds.email)
            self.password_input.setText(creds.password)
            self.delete_btn.show()
    
    def _save_credentials(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Erro", "Preencha email e senha!")
            return
        
        save_credentials(self.provider_domain, email, password)
        self.credentials = (email, password)
        QMessageBox.information(self, "Sucesso", f"Credenciais salvas para {self.provider_name}!")
        self.accept()
    
    def _delete_credentials(self):
        reply = QMessageBox.question(
            self, "Confirmar", 
            f"Remover credenciais de {self.provider_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_credentials(self.provider_domain)
            self.email_input.clear()
            self.password_input.clear()
            self.delete_btn.hide()
            QMessageBox.information(self, "Removido", "Credenciais removidas!")
    
    def get_credentials(self):
        return self.credentials


def show_login_dialog(provider_name: str, provider_domain: str, parent=None) -> tuple | None:
    dialog = LoginDialog(provider_name, provider_domain, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_credentials()
    return None
