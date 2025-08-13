import os
import requests
import json
from typing import List
from urllib.parse import urlparse
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
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] in ['obra', 'obras']:
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")
    
    def _default_headers(self):
        return {
            "Accept": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Referer": "https://mediocretoons.com/",
            "Origin": "https://mediocretoons.com",
        }

    def getManga(self, link: str) -> Manga:
        obra_id = self._extract_id(link)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        return Manga(
            id=str(data['id']),
            name=str(data['nome']),
        )

    def getChapters(self, obra_id: str) -> List[Chapter]:
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = self._default_headers()
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        chapters = []
        for ch in data.get('capitulos', []):
            chapters.append(
                Chapter(
                    id=str(ch['id']),
                    number=str(ch.get('numero', None)),
                    name=ch.get('nome'),
                )
            )
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        url = f'{self.BASE_API}/capitulos/{chapter.id}'
        headers_api = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            "Accept": "gzip, deflate, br, zstd",
            "Referer": "https://mediocretoons.com/",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        resp = requests.get(url, headers=headers_api)
        resp.raise_for_status()
        data = resp.json()

        paginas = data.get('paginas', [])

        # Monta a URL completa de cada imagem
        urls = [
            f"https://storage.mediocretoons.com/obras/{data['obr_id']}/capitulos/{data['cap_id']}/{page.get('src','')}"
            for page in paginas
        ]

        return Pages(
            id=str(data['cap_id']),
            number=str(data.get('cap_num', '')),
            name=chapter.name,
            pages=urls,  # aqui vai a lista de URLs completas
        )


