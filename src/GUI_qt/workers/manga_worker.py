from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from core.config.login_data import delete_login
from core.providers.application.use_cases import ProviderMangaUseCase, ProviderGetChaptersUseCase, ProviderLoginUseCase


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
        """Executes manga retrieval with robust error handling"""
        try:
            print(f"[MANGA_TASK] Starting manga search: {self.link}")
            
            # Login if necessary
            if self.provider.has_login:
                try:
                    print(f"[MANGA_TASK] Logging in to {self.provider.name}")
                    ProviderLoginUseCase(self.provider).execute()
                    print(f"[MANGA_TASK] ✅ Login successful")
                except Exception as e:
                    print(f"[MANGA_TASK] ❌ Login error: {e}")
                    self.signal.error.emit(f"Login error for {self.provider.name}: {str(e)}")
                    return
                    
            # Obter manga
            try:
                print(f"[MANGA_TASK] Obtaining manga data...")
                manga = ProviderMangaUseCase(self.provider).execute(self.link)
                
                # Verificar se manga é válido
                if manga is None:
                    print(f"[MANGA_TASK] ❌ Provider returned None")
                    self.signal.error.emit(f"Provider {self.provider.name} returned empty data for: {self.link}")
                    return
                
                # Verificar atributos obrigatórios
                if not hasattr(manga, 'id') or not hasattr(manga, 'name'):
                    print(f"[MANGA_TASK] ❌ Manga without required attributes: {manga}")
                    self.signal.error.emit(f"Invalid data returned by provider {self.provider.name}")
                    return
                
                # Verificar se valores não estão vazios
                if not manga.id or not manga.name:
                    print(f"[MANGA_TASK] ❌ Manga with empty values - ID: '{manga.id}', Name: '{manga.name}'")
                    self.signal.error.emit(f"Provider {self.provider.name} returned incomplete data")
                    return

                print(f"[MANGA_TASK] ✅ Manga obtained successfully: {manga.name}")
                self.signal.finished.emit(manga)
                
            except Exception as e:
                print(f"[MANGA_TASK] ❌ Error obtaining manga: {e}")
                import traceback
                traceback.print_exc()
                self.signal.error.emit(f"Error in scraper {self.provider.name}: {str(e)}")
                delete_login(self.provider.domain[0])
                
        except Exception as e:
            print(f"[MANGA_TASK] 💥 Critical error in worker: {e}")
            import traceback
            traceback.print_exc()
            try:
                delete_login(self.provider.domain[0])
                self.signal.error.emit(f"Critical error in {self.provider.name}: {str(e)}")
            except Exception as cleanup_error:
                print(f"[MANGA_TASK] Error in cleanup: {cleanup_error}")
                # Último recurso - tentar emitir erro básico
                try:
                    self.signal.error.emit(f"Critical failure in scraper")
                except:
                    print("[MANGA_TASK] Impossible to emit error signal")


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
        """Executa a obtenção de capítulos com tratamento robusto de erros"""
        try:
            print(f"[CHAPTERS_TASK] Starting chapters search: {self.id}")
            
            try:
                chapters = ProviderGetChaptersUseCase(self.provider).execute(self.id)
                
                # Verificar se capítulos é válido
                if chapters is None:
                    print(f"[CHAPTERS_TASK] ❌ Provider returned None for chapters")
                    self.signal.error.emit(f"Provider {self.provider.name} did not return chapters for: {self.id}")
                    return
                
                # Verificar se é uma lista
                if not isinstance(chapters, list):
                    print(f"[CHAPTERS_TASK] ❌ Chapters is not a list: {type(chapters)}")
                    self.signal.error.emit(f"Provider {self.provider.name} returned invalid format for chapters")
                    return
                
                # Verificar se lista não está vazia
                if len(chapters) == 0:
                    print(f"[CHAPTERS_TASK] ⚠️ Chapters list is empty")
                    self.signal.error.emit(f"No chapters found for this manga in {self.provider.name}")
                    return

                print(f"[CHAPTERS_TASK] ✅ {len(chapters)} chapters obtained successfully")
                self.signal.finished.emit(chapters)
                
            except Exception as e:
                print(f"[CHAPTERS_TASK] ❌ Error obtaining chapters: {e}")
                import traceback
                traceback.print_exc()
                self.signal.error.emit(f"Error in scraper {self.provider.name}: {str(e)}")
                delete_login(self.provider.domain[0])
                
        except Exception as e:
            print(f"[CHAPTERS_TASK] 💥 Critical error in worker: {e}")
            import traceback
            traceback.print_exc()
            try:
                delete_login(self.provider.domain[0])
                self.signal.error.emit(f"Critical error in {self.provider.name}: {str(e)}")
            except Exception as cleanup_error:
                print(f"[CHAPTERS_TASK] Error in cleanup: {cleanup_error}")
                # Último recurso - tentar emitir erro básico
                try:
                    self.signal.error.emit(f"Critical failure in scraper")
                except:
                    print("[CHAPTERS_TASK] Impossible to emit error signal")
