import logging
import os
import requests
from urllib.parse import urlparse
from typing import List
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.base import Base
from core.download.application.use_cases import DownloadUseCase

# Configurar logging para salvar em arquivo
log_path = os.path.join(os.getcwd(), "mediocretoons_provider.log")
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MediocretoonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt'
    domain = ['mediocretoons.com']
    has_login = False

    BASE_API = 'https://api.mediocretoons.com'
    BASE_CDN = 'https://storage.mediocretoons.com/obras'

    def _extract_id(self, url: str) -> str:
        logging.debug(f"_extract_id chamado com URL: {url}")
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] in ['obra', 'obras']:
            logging.debug(f"ID extraído: {parts[1]}")
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")
    
    def _default_headers(self):
        logging.debug("_default_headers chamado")
        return {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }

    def getManga(self, link: str) -> Manga:
        logging.info(f"getManga chamado com link: {link}")
        obra_id = self._extract_id(link)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        logging.info(f"GET {url} status_code: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"Dados recebidos getManga: {data}")

        manga = Manga(
            id=str(data['id']),
            name=str(data['nome']),
        )
        logging.info(f"Manga criado: {manga}")
        return manga

    def getChapters(self, obra_id: str) -> List[Chapter]:
        logging.info(f"getChapters chamado com obra_id: {obra_id}")
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        logging.info(f"GET {url} status_code: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"Dados recebidos getChapters: {data}")

        chapters = []
        for ch in data.get('capitulos', []):
            chapter = Chapter(
                id=str(ch['id']),
                number=str(ch.get('numero', None)),
                name=ch.get('nome'),
            )
            chapters.append(chapter)
            logging.info(f"Chapter criado: {chapter}")
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        logging.info(f"getPages chamado com chapter: {chapter}")
        url = f'{self.BASE_API}/capitulos/{chapter.id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        logging.info(f"GET {url} status_code: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"Dados recebidos getPages: {data}")

        paginas = data.get('paginas', [])
        urls = [
            f"https://storage.mediocretoons.com/obras/{data['obr_id']}/capitulos/{data['cap_id']}/{page.get('src', '')}"
            for page in paginas
        ]
        logging.info(f"URLs de páginas montadas: {urls}")

        pages = Pages(
            id=str(data['cap_id']),
            number=str(data.get('cap_num', '')),
            name=chapter.name,
            pages=urls,
        )
        logging.info(f"Pages criado: {pages}")
        return pages
    
    def download(self, pages: Pages, fn: any = None, headers=None, cookies=None):
        logging.info(f"download chamado com Pages: {pages}")
        if headers is None:
            headers = self._default_headers()
        result = DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
        logging.info(f"download finalizado com resultado: {result}")
        return result
