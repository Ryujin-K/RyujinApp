import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class AurorascanProvider(Base):
    name = 'Aurora Scan'
    lang = 'pt_Br'
    domain = ['www.serenitytoons.win', 'serenitytoons.win']

    def __init__(self) -> None:
        self.base = 'https://api.sussytoons.wtf'
        self.CDN = 'https://cdn.sussytoons.site'
        self.webBase = 'https://www.serenitytoons.win'
        self._default_host = self.domain[0]
        self._current_host: str = self._default_host
        self._host_cache: Dict[str, str] = {}
        self._manga_cache: Dict[str, Dict] = {}

    def _resolve_host(self, url: Optional[str]) -> str:
        if not url:
            return self._current_host or self._default_host

        parsed = urlparse(url)
        host = parsed.hostname
        if host:
            self._current_host = host
        return self._current_host or self._default_host

    def _store_host(self, manga_id: Optional[str], host: str) -> None:
        if manga_id:
            self._host_cache[str(manga_id)] = host

    def _headers(self, manga_id: Optional[str] = None) -> Dict[str, str]:
        host = self._host_cache.get(str(manga_id)) if manga_id else None
        if not host:
            host = self._current_host or self._default_host
        return {'scan-id': host}

    def _manga_id_from_url(self, link: str) -> Optional[str]:
        match = re.search(r'/obra/(\d+)', link)
        return match.group(1) if match else None

    def _fetch_manga_data(self, manga_id: str) -> Dict:
        if manga_id in self._manga_cache:
            return self._manga_cache[manga_id]

        response = Http.get(f'{self.base}/obras/{manga_id}', headers=self._headers(manga_id))
        data = response.json().get('resultado', {})
        if data:
            self._manga_cache[manga_id] = data
        return data

    def getManga(self, link: str) -> Manga:
        manga_id = self._manga_id_from_url(link)
        host = self._resolve_host(link)
        self._store_host(manga_id, host)

        if not manga_id:
            raise ValueError('Link de obra inválido para Aurora Scan')

        data = self._fetch_manga_data(manga_id)
        title = data.get('obr_nome') or 'Mangá'
        return Manga(link, title)

    def getChapters(self, link: str) -> List[Chapter]:
        manga_id = self._manga_id_from_url(link)
        host = self._resolve_host(link)
        self._store_host(manga_id, host)

        if not manga_id:
            raise ValueError('Link de obra inválido para Aurora Scan')

        data = self._fetch_manga_data(manga_id)
        title = data.get('obr_nome', 'Mangá')

        chapters: List[Chapter] = []
        for chapter in data.get('capitulos', []):
            cap_id = chapter.get('cap_id')
            cap_name = chapter.get('cap_nome') or f"Capítulo {chapter.get('cap_numero')}"
            chapters.append(Chapter([manga_id, cap_id], cap_name, title))

        return chapters

    def getPages(self, ch: Chapter) -> Pages:
        cap_id: Optional[str]
        manga_id: Optional[str] = None

        if isinstance(ch.id, (list, tuple)):
            manga_id = str(ch.id[0]) if len(ch.id) > 0 else None
            cap_id = ch.id[1] if len(ch.id) > 1 else ch.id[0]
        else:
            cap_id = ch.id

        if not cap_id:
            raise ValueError('Identificador de capítulo inválido')

        headers = self._headers(manga_id)
        data = Http.get(f'{self.base}/capitulos/{cap_id}', headers=headers).json().get('resultado', {})
        paginas = data.get('cap_paginas') or []

        images: List[str] = []
        cdn_base = self.CDN.rstrip('/')

        for pagina in paginas:
            src = (pagina.get('src') or '').strip()
            path = (pagina.get('path') or '').strip('/ ')

            if not src:
                continue

            if src.startswith('http'):
                images.append(src)
                continue

            combined_path = '/'.join(part for part in [path, src.lstrip('/')] if part)
            images.append(f'{cdn_base}/{combined_path}')

        if not images:
            raise RuntimeError('Nenhuma página disponível para este capítulo')

        return Pages(ch.id, ch.number, ch.name, images)

    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        effective_headers = {}
        if isinstance(headers, dict):
            effective_headers.update(headers)

        effective_headers.setdefault('Referer', self.webBase)
        effective_headers.setdefault('Origin', self.webBase)
        effective_headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8')

        return super().download(pages=pages, fn=fn, headers=effective_headers, cookies=cookies)