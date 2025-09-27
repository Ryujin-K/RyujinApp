import os
import sys
import json
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QLocale
from GUI_qt.utils.paths import paths
from GUI_qt.utils.config import get_config, update_lang
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

current_dir = str(paths.gui_dir)
assets = str(paths.assets_dir)

class LoadingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RyujinApp")
        self.setFixedSize(300, 100)
        self.setWindowIcon(QIcon(os.path.join(assets, 'icon.ico')))

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
        
        layout = QVBoxLayout()
        self.label = QLabel(translation['updates'])
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)