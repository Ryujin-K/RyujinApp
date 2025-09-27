import re
import os
import json
from typing import List
from PyQt6 import uic
from PyQt6.QtWidgets import QSpacerItem, QSizePolicy
from core.providers.domain.entities import Chapter
from GUI_qt.utils.config import get_config
from GUI_qt.utils.paths import paths


def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")


class ChapterManager:
    def __init__(self, parent_window, download_callback=None):
        self.parent_window = parent_window
        self.download_callback = download_callback
        self.chapters = []
        self.all_chapters = []
        self.current_dir = str(paths.gui_dir)
        self.assets = os.path.join(self.current_dir, 'assets')
        self.vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    def set_chapters(self, chapters: List[Chapter]):
        log_info(f"Definindo capítulos: {len(chapters)} capítulos recebidos")
        try:
            self.chapters = chapters
            self.all_chapters = chapters
            self._add_chapters()
            log_success(f"Capítulos definidos com sucesso")
        except Exception as e:
            log_error(f"Falha ao definir capítulos: {str(e)}")
            raise

    def filter_chapters(self, search_text: str):
        log_info(f"Filtrando capítulos com texto: '{search_text}'")
        
        def extract_number(chapter_number):
            match = re.search(r'\d+(\.\d+)?', chapter_number)
            return float(match.group()) if match else None

        text = search_text.strip()
        try:
            if not text:
                log_info("Texto vazio, mostrando todos os capítulos")
                self.chapters = self.all_chapters
                self._add_chapters()
                log_success(f"Filtro limpo: {len(self.chapters)} capítulos mostrados")
                return

            if match := re.match(r'(\d+(\.\d+)?)\*', text):
                number = float(match.group(1))
                self.chapters = [chapter for chapter in self.all_chapters 
                               if (extracted := extract_number(chapter.number)) is not None and extracted >= number]
                log_success(f"Filtro 'maior que {number}': {len(self.chapters)} capítulos encontrados")

            elif match := re.match(r'(\d+(\.\d+)?)-(\d+(\.\d+)?)', text):
                start, end = float(match.group(1)), float(match.group(3))
                self.chapters = [chapter for chapter in self.all_chapters 
                               if (extracted := extract_number(chapter.number)) is not None and start <= extracted <= end]
                log_success(f"Filtro de intervalo '{start}-{end}': {len(self.chapters)} capítulos encontrados")

            else:
                self.chapters = [chapter for chapter in self.all_chapters if text in chapter.number]
                log_success(f"Filtro de texto '{text}': {len(self.chapters)} capítulos encontrados")

        except ValueError as e:
            log_error(f"Erro no filtro de capítulos: {e}")
            print(f"Error: {e}")
            self.chapters = []

        self._add_chapters()

    def invert_chapters(self):
        log_info(f"Invertendo ordem dos capítulos: {len(self.chapters)} capítulos")
        try:
            self.chapters = self.chapters[::-1]
            self._add_chapters()
            log_success(f"Capítulos invertidos com sucesso")
        except Exception as e:
            log_error(f"Falha ao inverter capítulos: {str(e)}")
            raise

    def _add_chapters(self):
        log_info(f"Renderizando {len(self.chapters)} capítulos na interface")
        
        try:
            # Limpa widgets existentes
            removed_count = 0
            while self.parent_window.verticalChapter.count():
                item = self.parent_window.verticalChapter.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                    removed_count += 1
            
            if removed_count > 0:
                log_info(f"Removidos {removed_count} widgets antigos")

            # Carrega configurações e traduções
            config = get_config()
            with open(os.path.join(self.assets, 'translations.json'), 'r', encoding='utf-8') as file:
                translations = json.load(file)
            download_text = translations[config.lang]['download']

            # Adiciona novos capítulos
            added_count = 0
            for chapter in self.chapters:
                chapter_ui = uic.loadUi(os.path.join(self.assets, 'chapter.ui'))
                chapter_ui.numberLabel.setText(str(chapter.number))
                
                if hasattr(self.parent_window, 'download_status'):
                    if any(ch.id == chapter.id for ch, _, _ in self.parent_window.download_status):
                        chapter_ui.download.setEnabled(False)

                if self.download_callback:
                    chapter_ui.download.clicked.connect(
                        lambda _, ch=chapter, btn=chapter_ui.download: 
                        self.download_callback(ch, btn)
                    )
                chapter_ui.download.setText(download_text)
                self.parent_window.verticalChapter.addWidget(chapter_ui)
                added_count += 1
            
            # Adiciona espaçador
            self.parent_window.verticalChapter.addItem(self.vertical_spacer)

            log_success(f"Interface renderizada com sucesso: {added_count} capítulos adicionados")

        except Exception as e:
            log_error(f"Falha ao renderizar capítulos: {str(e)}")
            raise
