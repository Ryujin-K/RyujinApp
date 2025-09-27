import os
import sys
import json
import webbrowser
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QLocale
from GUI_qt.utils.git import get_last_version
from GUI_qt.utils.paths import paths
from GUI_qt.utils.config import get_config, update_lang
from PyQt6.QtWidgets import QMessageBox

current_dir = str(paths.gui_dir)
assets = str(paths.assets_dir)

class NewVersion():
    def __init__(self):
        self.msg_box = QMessageBox()
        self.show_message_box()

    def show_message_box(self):
        translations = {}
        with open(os.path.join(assets, 'translations.json'), 'r', encoding='utf-8') as file:
            translations = json.load(file)

        config = get_config()
        if not config:
            language = QLocale.system().name()
            update_lang(language)
        else:
            language = config.lang
        if language not in translations:
            language = 'en'
        
        translation = translations[language]

        self.msg_box.setWindowIcon(QIcon(os.path.join(assets, 'icon.ico')))
        self.msg_box.setWindowTitle(translation['new_version'])
        self.msg_box.setText(translation['new_version_description'])
        self.msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        self.msg_box.button(QMessageBox.StandardButton.Ok).clicked.connect(self.open_website)
        self.msg_box.button(QMessageBox.StandardButton.Cancel).clicked.connect(self.close_application)
        
        self.msg_box.exec()

    def open_website(self):
        version = get_last_version()
        webbrowser.open(f'https://github.com/Ryujin-K/RyujinApp/releases/tag/v{version}')
        self.msg_box.close()
    
    def close_application(self):
        self.msg_box.close()

