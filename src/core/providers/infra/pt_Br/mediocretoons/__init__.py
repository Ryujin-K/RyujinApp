import os
import requests
import json
from typing import List
from urllib.parse import urlparse
from core.download.application.use_cases import DownloadUseCase
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.base import Base


class MediocretoonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt'
    domain = ['mediocretoons.com']
    has_login = False

    BASE_API = 'https://api.mediocretoons.com'
    BASE_CDN = 'https://storage.mediocretoons.com/obras'

    def _extract_id(self, url: str) -> str:
        print("[LOG] _extract_id chamado com URL:", url)
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] in ['obra', 'obras']:
            print("[LOG] ID extraído:", parts[1])
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")
    
    def _default_headers(self):
        print("[LOG] _default_headers chamado")
        return {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }

    def getManga(self, link: str) -> Manga:
        print("[LOG] getManga chamado com link:", link)
        obra_id = self._extract_id(link)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        print(f"[LOG] GET {url} status_code:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        print("[LOG] Dados recebidos getManga:", data)

        manga = Manga(
            id=str(data['id']),
            name=str(data['nome']),
        )
        print("[LOG] Manga criado:", manga)
        return manga

    def getChapters(self, obra_id: str) -> List[Chapter]:
        print("[LOG] getChapters chamado com obra_id:", obra_id)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        print(f"[LOG] GET {url} status_code:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        print("[LOG] Dados recebidos getChapters:", data)

        chapters = []
        for ch in data.get('capitulos', []):
            chapter = Chapter(
                id=str(ch['id']),
                number=str(ch.get('numero', None)),
                name=ch.get('nome'),
            )
            chapters.append(chapter)
            print("[LOG] Chapter criado:", chapter)
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        print("[LOG] getPages chamado com chapter:", chapter)
        url = f'{self.BASE_API}/capitulos/{chapter.id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        print(f"[LOG] GET {url} status_code:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        print("[LOG] Dados recebidos getPages:", data)

        paginas = data.get('paginas', [])
        urls = [
            f"https://storage.mediocretoons.com/obras/{data['obr_id']}/capitulos/{data['cap_id']}/{page.get('src', '')}"
            for page in paginas
        ]
        print("[LOG] URLs de páginas montadas:", urls)

        pages = Pages(
            id=str(data['cap_id']),
            number=str(data.get('cap_num', '')),
            name=chapter.name,
            pages=urls,
        )
        print("[LOG] Pages criado:", pages)
        return pages
    
    def download(self, pages: Pages, fn: any = None, headers=None, cookies=None):
        print("[LOG] download chamado com Pages:", pages)
        if headers is None:
            headers = self._default_headers()
        result = DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
        print("[LOG] download finalizado com resultado:", result)
        return result

