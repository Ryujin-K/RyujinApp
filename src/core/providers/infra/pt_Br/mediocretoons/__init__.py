import requests
from typing import List
from core.download.application.use_cases import DownloadUseCase
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.domain.provider_repository import ProviderRepository
from core.providers.infra.template.base import Base
from urllib.parse import urlparse, parse_qs

class MediocretoonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt'
    domain = ['mediocretoons.com']
    has_login = False

    BASE_API = 'https://api.mediocretoons.com'

    def getManga(self, link: str) -> Manga:
        # extrair id da obra da URL (ex: https://mediocretoons.com/obra/295)
        obra_id = self._extract_id(link)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']

        # Monta o Manga com os dados relevantes
        manga = Manga(
            id=str(data['id']),
            title=data['nome'],
        )
        return manga

    def getChapters(self, obra_id: str) -> List[Chapter]:
        # pega capítulos da obra via endpoint (por exemplo, /obras/{id} já retorna capítulos)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']

        chapters_json = data.get('capitulos', [])
        chapters = []
        for ch in chapters_json:
            chapter = Chapter(
                id=str(ch['id']),
                title=ch.get('nome', f"Capítulo {ch['id']}"),
                number=ch.get('cap_num', None),
                # complete com outros atributos necessários
            )
            chapters.append(chapter)
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        # pega as páginas do capítulo por id
        url = f'{self.BASE_API}/capitulos/{chapter.id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']

        # 'cap_paginas' tem as imagens em JSON string, então vamos carregar
        import json
        paginas = json.loads(data.get('cap_paginas', '[]'))

        # montar a lista de URLs das imagens
        urls = [f"https://storage.mediocretoons.com/obra/{data['obr_id']}/capitulos/{data['cap_id']}/{page['src']}" for page in paginas]

        pages = Pages(
            urls=urls,
            # mais campos se precisar
        )
        return pages

    def _extract_id(self, url: str) -> str:
        # exemplo para extrair id da URL: https://mediocretoons.com/obra/295
        path = urlparse(url).path  # ex: /obra/295
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'obra':
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")

