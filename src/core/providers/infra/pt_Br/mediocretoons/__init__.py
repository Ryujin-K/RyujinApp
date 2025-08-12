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

    def _extract_id(self, url: str) -> str:
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] in ['obra', 'obras']:
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")

    def getManga(self, link: str) -> Manga:
        obra_id = self._extract_id(link)
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']

        manga = Manga(
            id=str(data['id']),
            title=data['nome'],
        )
        return manga

    def getChapters(self, obra_id: str) -> List[Chapter]:
        url = f'{self.BASE_API}/obras/{obra_id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
            )
            chapters.append(chapter)
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        url = f'{self.BASE_API}/capitulos/{chapter.id}'
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://mediocretoons.com",
            "Origin": "https://mediocretoons.com",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']

        paginas = json.loads(data.get('cap_paginas', '[]'))

        urls = []
        for page in paginas:
            src = page.get('src', '')
            if src.startswith('http'):
                urls.append(src)
            else:
                urls.append(f"https://storage.mediocretoons.com/obra/{data['obr_id']}/capitulos/{data['cap_id']}/{src}")

        pages = Pages(
            urls=urls,
        )
        return pages
