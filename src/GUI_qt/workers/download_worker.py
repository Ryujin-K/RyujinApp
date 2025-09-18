import os
import traceback
from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from core.config.img_conf import get_config as get_img_config
from core.config.login_data import delete_login
from core.providers.application.use_cases import ProviderGetPagesUseCase, ProviderDownloadUseCase
from core.slicer.application.use_cases import SlicerUseCase
from core.group_imgs.application.use_cases import GroupImgsUseCase
from GUI_qt.utils.config import get_config
from GUI_qt.utils.load_providers import base_path
import json


class DownloadWorkerSignals(QObject):
    progress_changed = pyqtSignal(int)
    download_error = pyqtSignal(str)
    color = pyqtSignal(str)
    name = pyqtSignal(str)


class DownloadWorker(QRunnable):
    def __init__(self, chapter, provider):
        super().__init__()
        self.chapter = chapter
        self.provider = provider
        self.signals = DownloadWorkerSignals()
        self.assets = os.path.join(base_path(), "GUI_qt", "assets")

    def run(self):
        try:
            print(f"[DOWNLOAD] 🚀 Starting download: {self.chapter.number} ({self.provider.name})")

            img_conf = get_img_config()
            conf = get_config()
            
            try:
                print(f"[DOWNLOAD] 📥 Obtaining pages for chapter {self.chapter.number}...")
                pages = ProviderGetPagesUseCase(self.provider).execute(self.chapter)
                print(f"[DOWNLOAD] ✅ {len(pages.pages)} pages found.")

            except Exception as e:
                print(f"[DOWNLOAD] ❌ Error obtaining pages: {str(e)}")
                traceback.print_exc()
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Error obtaining pages: {str(e)}')
                return
            
            translations = {}
            with open(os.path.join(self.assets, 'translations.json'), 'r', encoding='utf-8') as file:
                translations = json.load(file)
            language = conf.lang
            if language not in translations: language = 'en'
            translation = translations[language]
            self.signals.name.emit(translation['downloading'])

            def set_progress_bar_style(color):
                self.signals.color.emit(f"QProgressBar::chunk {{ background-color: {color}; }}")

            set_progress_bar_style("#32CD32")
            
            def update_progress_bar(value):
                try:
                    self.signals.progress_changed.emit(int(value))
                except Exception as e:
                    print(f"[DOWNLOAD] ⚠️ Progress bar error: {e}")

            try:
                print(f"[DOWNLOAD] 💾 Downloading {len(pages.pages)} images...")
                ch = ProviderDownloadUseCase(self.provider).execute(pages=pages, fn=update_progress_bar)
                print(f"[DOWNLOAD] ✅ Download completed: {self.chapter.number}")

            except Exception as e:
                print(f"[DOWNLOAD] ❌ Error downloading: {str(e)}")
                traceback.print_exc()
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no download: {str(e)}')
                delete_login(self.provider.domain[0])
                return

            if img_conf.slice:
                print(f"[DOWNLOAD] ✂️ Starting slicer for: {self.chapter.number}")
                self.signals.name.emit(translation['slicing'])
                self.signals.progress_changed.emit(0)
                set_progress_bar_style("#0080FF")
                ch = SlicerUseCase().execute(ch, update_progress_bar)
                print(f"[DOWNLOAD] ✅ Slicer completed: {self.chapter.number}")

            if img_conf.group:
                print(f"[DOWNLOAD] 📦 Starting grouping for: {self.chapter.number}")
                self.signals.name.emit(translation['grouping'])
                self.signals.progress_changed.emit(0)
                set_progress_bar_style("#FFA500")
                GroupImgsUseCase().execute(ch, update_progress_bar)
                self.signals.progress_changed.emit(100)
                print(f"[DOWNLOAD] ✅ Grouping completed: {self.chapter.number}")

            print(f"[DOWNLOAD] 🎉 Processing complete: {self.chapter.number}")

        except Exception as e:
            print(f"[DOWNLOAD] 💥 Critical error: {self.chapter.number} - {str(e)}")
            traceback.print_exc()
            try:
                set_progress_bar_style("red")
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n General error: {str(e)}')
                delete_login(self.provider.domain[0])
            except:
                pass