from typing import List
from core.download.application.use_cases import DownloadUseCase
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.domain.provider_repository import ProviderRepository
from core.providers.infra.template.scraper_logger import ScraperLogger, log_method

class Base(ProviderRepository):
    name = ''
    lang = ''
    domain = ['']
    has_login = False

    def __init__(self):
        # Configurar nome do provider para logs se não estiver definido
        if not self.name:
            self.name = self.__class__.__name__
        ScraperLogger.info(self.name, "init", "Provider inicializado", 
                          lang=self.lang, domains=str(self.domain))

    def login() -> None:
        raise NotImplementedError()

    @log_method("getManga")
    def getManga(link: str) -> Manga:
        raise NotImplementedError()

    @log_method("getChapters")  
    def getChapters(id: str) -> List[Chapter]:
        raise NotImplementedError()
    
    @log_method("getPages")
    def getPages(ch: Chapter) -> Pages:
        raise NotImplementedError()
    
    @log_method("download")
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
