import os
import traceback
import time 
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
        self.current_dir = os.path.join(base_path(), 'GUI_qt')
        self.assets = os.path.join(self.current_dir, 'assets')

    def run(self):
        try:
            print(f"\n[DEBUG] Início do DownloadWorker para o capítulo: {self.chapter.number} do provedor {self.provider.name}")
            time.sleep(0.1)

            img_conf = get_img_config()
            conf = get_config()
            
            try:
                print("[DEBUG] Passo 1: Obtendo a lista de páginas...")
                time.sleep(0.1)

                pages = ProviderGetPagesUseCase(self.provider).execute(self.chapter)

                print(f"[DEBUG] Passo 1 concluído. {len(pages.pages)} páginas encontradas.")
                time.sleep(0.1)

            except Exception as e:
                print("\n--- ERRO OCORREU EM 'ProviderGetPagesUseCase' ---")
                traceback.print_exc()
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro ao obter páginas: {str(e)}')
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
                    print(f"Erro ao atualizar barra de progresso: {e}")

            try:
                print("[DEBUG] Passo 2: Iniciando o download das imagens...")
                time.sleep(0.1)

                ch = ProviderDownloadUseCase(self.provider).execute(pages=pages, fn=update_progress_bar)

                print("[DEBUG] Passo 2 concluído. Download finalizado.")
                time.sleep(0.1)

            except Exception as e:
                print("\n--- ERRO OCORREU EM 'ProviderDownloadUseCase' ---")
                traceback.print_exc()
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no download: {str(e)}')
                delete_login(self.provider.domain[0])
                return

            if img_conf.slice:
                print("[DEBUG] Passo 3: Iniciando o Slicer...")
                time.sleep(0.1)
                self.signals.name.emit(translation['slicing'])
                self.signals.progress_changed.emit(0)
                set_progress_bar_style("#0080FF")
                ch = SlicerUseCase().execute(ch, update_progress_bar)

            if img_conf.group:
                print("[DEBUG] Passo 4: Iniciando o Agrupamento...")
                time.sleep(0.1)
                self.signals.name.emit(translation['grouping'])
                self.signals.progress_changed.emit(0)
                set_progress_bar_style("#FFA500")
                GroupImgsUseCase().execute(ch, update_progress_bar)
                self.signals.progress_changed.emit(100)
            
            print(f"[DEBUG] Fim do DownloadWorker para o capítulo: {self.chapter.number}. Tudo concluído.")
            time.sleep(0.1)

        except Exception as e:
            print("\n--- ERRO GERAL CRÍTICO NO DOWNLOAD WORKER ---")
            traceback.print_exc()
            try:
                set_progress_bar_style("red")
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro geral: {str(e)}')
                delete_login(self.provider.domain[0])
            except:
                pass