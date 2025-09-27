from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from core.config.login_data import delete_login
from core.providers.application.use_cases import ProviderMangaUseCase, ProviderGetChaptersUseCase, ProviderLoginUseCase


def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_success(message):
    print(f"[SUCCESS] {message}")


class MangaTaskSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class MangaTask(QRunnable):
    def __init__(self, provider, link):
        super().__init__()
        self.provider = provider
        self.link = link
        self.signal = MangaTaskSignals()

    def run(self):
        log_info(f"Iniciando MangaTask para {self.provider.name} - Link: {self.link}")
        
        try:
            # Login se necessário
            if self.provider.has_login:
                log_info(f"Fazendo login para {self.provider.name}...")
                try:
                    ProviderLoginUseCase(self.provider).execute()
                    log_success(f"Login realizado com sucesso para {self.provider.name}")
                except Exception as e:
                    log_error(f"Falha no login para {self.provider.name}: {str(e)}")
                    self.signal.error.emit(f"Erro no login: {str(e)}")
                    return
            else:
                log_info(f"Provider {self.provider.name} não requer login")
                    
            # Obter dados do manga
            log_info(f"Obtendo dados do manga...")
            try:
                manga = ProviderMangaUseCase(self.provider).execute(self.link)
                log_success(f"Manga obtido com sucesso: {manga.name if hasattr(manga, 'name') else 'Sem nome'}")
                self.signal.finished.emit(manga)
            except Exception as e:
                log_error(f"Falha ao obter manga: {str(e)}")
                self.signal.error.emit(f"Erro ao obter manga: {str(e)}")
                delete_login(self.provider.domain[0])
                
        except Exception as e:
            log_error(f"Erro geral no MangaTask: {str(e)}")
            try:
                delete_login(self.provider.domain[0])
                self.signal.error.emit(f"Erro geral: {str(e)}")
            except Exception as cleanup_error:
                log_error(f"Erro no cleanup: {cleanup_error}")
                print(f"Erro no MangaTask: {e}")
                print(f"Erro no cleanup: {cleanup_error}")
                try:
                    self.signal.error.emit(f"Erro crítico: {str(e)}")
                except:
                    pass


class ChaptersTaskSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class ChaptersTask(QRunnable):
    def __init__(self, provider, id):
        super().__init__()
        self.provider = provider
        self.id = id
        self.signal = ChaptersTaskSignals()

    def run(self):
        log_info(f"Iniciando ChaptersTask para {self.provider.name} - ID: {self.id}")
        
        try:
            log_info(f"Obtendo capítulos...")
            try:
                chapters = ProviderGetChaptersUseCase(self.provider).execute(self.id)
                chapter_count = len(chapters) if chapters else 0
                log_success(f"Capítulos obtidos com sucesso: {chapter_count} capítulos encontrados")
                self.signal.finished.emit(chapters)
            except Exception as e:
                log_error(f"Falha ao obter capítulos: {str(e)}")
                self.signal.error.emit(f"Erro ao obter capítulos: {str(e)}")
                delete_login(self.provider.domain[0])
                
        except Exception as e:
            log_error(f"Erro geral no ChaptersTask: {str(e)}")
            try:
                delete_login(self.provider.domain[0])
                self.signal.error.emit(f"Erro geral: {str(e)}")
            except Exception as cleanup_error:
                log_error(f"Erro no cleanup: {cleanup_error}")
                print(f"Erro no ChaptersTask: {e}")
                print(f"Erro no cleanup: {cleanup_error}")
                try:
                    self.signal.error.emit(f"Erro crítico: {str(e)}")
                except:
                    pass
