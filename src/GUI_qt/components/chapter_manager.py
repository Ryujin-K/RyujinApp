import re
import os
import json
import traceback
from typing import List
from PyQt6 import uic
from PyQt6.QtWidgets import QSpacerItem, QSizePolicy
from core.providers.domain.entities import Chapter
from GUI_qt.utils.config import get_config
from GUI_qt.utils.load_providers import base_path


class ChapterManager:
    def __init__(self, parent_window, download_callback=None):
        self.parent_window = parent_window
        self.download_callback = download_callback
        self.chapters = []
        self.all_chapters = []
        self.current_dir = os.path.join(base_path(), 'GUI_qt')
        self.assets = os.path.join(self.current_dir, 'assets')
        self.vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    def set_chapters(self, chapters: List[Chapter]):
        print("[DEBUG_UI] Entrando em 'set_chapters'.") 
        self.chapters = chapters
        self.all_chapters = chapters
        self._add_chapters()

    def filter_chapters(self, search_text: str):
        def extract_number(chapter_number):
            match = re.search(r'\d+(\.\d+)?', chapter_number)
            return float(match.group()) if match else None

        text = search_text.strip()
        if not text:
            self.chapters = self.all_chapters
            self._add_chapters()
            return

        try:
            if match := re.match(r'(\d+(\.\d+)?)\*', text):
                number = float(match.group(1))
                self.chapters = [chapter for chapter in self.all_chapters 
                               if (extracted := extract_number(chapter.number)) is not None and extracted >= number]

            elif match := re.match(r'(\d+(\.\d+)?)-(\d+(\.\d+)?)', text):
                start, end = float(match.group(1)), float(match.group(3))
                self.chapters = [chapter for chapter in self.all_chapters 
                               if (extracted := extract_number(chapter.number)) is not None and start <= extracted <= end]

            else:
                self.chapters = [chapter for chapter in self.all_chapters if text in chapter.number]

        except ValueError as e:
            print(f"Error: {e}")
            self.chapters = []
        self._add_chapters()


    def invert_chapters(self):
        self.chapters = self.chapters[::-1]
        self._add_chapters()

    def _add_chapters(self):
        try:
            print("[DEBUG_UI] Entrando em '_add_chapters'.")
            
            while self.parent_window.verticalChapter.count():
                item = self.parent_window.verticalChapter.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
            print("[DEBUG_UI] Layout de capítulos limpo.")

            config = get_config()
            with open(os.path.join(self.assets, 'translations.json'), 'r', encoding='utf-8') as file:
                translations = json.load(file)
            download_text = translations[config.lang]['download']
            
            print("[DEBUG_UI] Iniciando loop para adicionar capítulos.")

            for i, chapter in enumerate(self.chapters):
                print(f"[DEBUG_UI] Adicionando capítulo {i+1}/{len(self.chapters)}: {chapter.number}")
                
                chapter_ui = uic.loadUi(os.path.join(self.assets, 'chapter.ui'))
                print("[DEBUG_UI] -> 'chapter.ui' carregado.")

                chapter_ui.numberLabel.setText(str(chapter.number))
                print("[DEBUG_UI] -> Label de texto definido.")
                
                if hasattr(self.parent_window, 'download_status'):
                    if any(ch.id == chapter.id for ch, _, _ in self.parent_window.download_status):
                        chapter_ui.download.setEnabled(False)

                if self.download_callback:
                    chapter_ui.download.clicked.connect(
                        lambda _, ch=chapter, btn=chapter_ui.download: 
                        self.download_callback(ch, btn)
                    )
                
                chapter_ui.download.setText(download_text)
                print("[DEBUG_UI] -> Botão de download configurado.")

                self.parent_window.verticalChapter.addWidget(chapter_ui)
                print("[DEBUG_UI] -> Widget adicionado ao layout vertical.")
            
            print("[DEBUG_UI] Loop de capítulos concluído.")
            self.parent_window.verticalChapter.addItem(self.vertical_spacer)
            print("[DEBUG_UI] Espaçador vertical adicionado. Fim de '_add_chapters'.")

        except Exception as e:
            print("\n--- ERRO FATAL EM '_add_chapters' AO ATUALIZAR A UI ---")
            traceback.print_exc()