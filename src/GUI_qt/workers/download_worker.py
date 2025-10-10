import os
from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from core.config.img_conf import get_config as get_img_config
from core.config.login_data import delete_login
from core.providers.application.use_cases import ProviderGetPagesUseCase, ProviderDownloadUseCase
from core.slicer.application.use_cases import SlicerUseCase
from core.group_imgs.application.use_cases import GroupImgsUseCase
from GUI_qt.utils.config import get_config
from GUI_qt.utils.paths import paths
import json


def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")


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
        self.current_dir = str(paths.gui_dir)
        self.assets = os.path.join(self.current_dir, 'assets')

    def run(self):
        log_info(f"Iniciando download: {self.chapter.name} - Cap. {self.chapter.number}")
        
        try:
            img_conf = get_img_config()
            conf = get_config()
            
            try:
                pages = ProviderGetPagesUseCase(self.provider).execute(self.chapter)
                page_count = len(pages.pages) if hasattr(pages, 'pages') else 0
                log_info(f"Obtendo {page_count} páginas...")
            except Exception as e:
                log_error(f"Falha ao obter páginas: {str(e)}")
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro ao obter páginas: {str(e)}')
                return
            
            translations = {}

            with open(os.path.join(self.assets, 'translations.json'), 'r', encoding='utf-8') as file:
                translations = json.load(file)

            language = conf.lang
            if language not in translations:
                language = 'en'

            translation = translations[language]
            self.signals.name.emit(translation['downloading'])

            def set_progress_bar_style(color):
                self.signals.color.emit(f"""
                    QProgressBar {{
                        text-align: center;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                    }}
                    QProgressBar::text {{
                        color: #fff;
                        font-weight: bold;
                    }}
                """)

            set_progress_bar_style("#32CD32")
            
            def update_progress_bar(value):
                try:
                    self.signals.progress_changed.emit(int(value))
                except Exception as e:
                    log_error(f"Erro ao atualizar barra de progresso: {e}")

            try:
                ch = ProviderDownloadUseCase(self.provider).execute(pages=pages, fn=update_progress_bar)
                log_success(f"Download concluído: Cap. {self.chapter.number}")
            except ZeroDivisionError as e:
                log_error(f"ZeroDivisionError no download: {str(e)}")
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro: Nenhuma página encontrada para download - ZeroDivisionError')
                return
            except Exception as e:
                log_error(f"Erro no download: {str(e)}")
                error_msg = "Nenhuma página encontrada - ZeroDivisionError" if "division by zero" in str(e).lower() else str(e)
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no download: {error_msg}')
                delete_login(self.provider.domain[0])
                return

            if img_conf.slice:
                try:
                    self.signals.name.emit(translation['slicing'])
                    self.signals.progress_changed.emit(0)
                    set_progress_bar_style("#0080FF")
                    ch = SlicerUseCase().execute(ch, update_progress_bar)
                    log_success(f"Slice concluído: Cap. {self.chapter.number}")
                except ZeroDivisionError as e:
                    log_error(f"ZeroDivisionError no slice: {str(e)}")
                    self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no slice: Nenhum arquivo para processar - ZeroDivisionError')
                    return
                except Exception as e:
                    log_error(f"Erro no slice: {str(e)}")
                    error_msg = "Nenhum arquivo para processar - ZeroDivisionError" if "division by zero" in str(e).lower() else str(e)
                    self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no slice: {error_msg}')
                    return

            if img_conf.group:
                try:
                    self.signals.name.emit(translation['grouping'])
                    self.signals.progress_changed.emit(0)
                    set_progress_bar_style("#FFA500")
                    GroupImgsUseCase().execute(ch, update_progress_bar)
                    self.signals.progress_changed.emit(100)
                    log_success(f"Agrupamento concluído: Cap. {self.chapter.number}")
                except ZeroDivisionError as e:
                    log_error(f"ZeroDivisionError no agrupamento: {str(e)}")
                    self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no agrupamento: Nenhum arquivo para agrupar - ZeroDivisionError')
                    return
                except Exception as e:
                    log_error(f"Erro no agrupamento: {str(e)}")
                    error_msg = "Nenhum arquivo para agrupar - ZeroDivisionError" if "division by zero" in str(e).lower() else str(e)
                    self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro no agrupamento: {error_msg}')
                    return

        except ZeroDivisionError as e:
            log_error(f"ZeroDivisionError geral capturado: {str(e)}")
            try:
                set_progress_bar_style("red")
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro: Dados inválidos ou vazios - ZeroDivisionError')
            except:
                log_error(f"Erro ao emitir sinal de erro de divisão por zero: {e}")
        except Exception as e:
            log_error(f"Erro geral capturado no DownloadWorker: {str(e)}")
            try:
                set_progress_bar_style("red")
                error_msg = "Dados inválidos ou vazios - ZeroDivisionError" if "division by zero" in str(e).lower() else str(e)
                self.signals.download_error.emit(f'{self.chapter.name} \n {self.chapter.number} \n Erro geral: {error_msg}')
                delete_login(self.provider.domain[0])
            except Exception as cleanup_error:
                log_error(f"Erro crítico no DownloadWorker: {e}")
                log_error(f"Erro no cleanup: {cleanup_error}")
                try:
                    self.signals.download_error.emit(f'Erro crítico: {str(e)}')
                except:
                    pass
