import re
import posixpath
from typing import List
from core.__seedwork.infra.http import Http
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class NewSussyToonsProvider(Base):
    name = 'New Sussy Toons'
    lang = 'pt_Br'
    domain = ['new.sussytoons.site', 'www.sussyscan.com', 'www.sussytoons.site', 'www.sussytoons.wtf', 'sussytoons.wtf']

    def __init__(self) -> None:
        self.base = 'https://api.sussytoons.wtf'
        self.CDN = 'https://cdn.sussytoons.site'
        self.old = 'https://oldi.sussytoons.site/wp-content/uploads/WP-manga/data/'
        self.oldCDN = 'https://oldi.sussytoons.site/scans/1/obras'
        self.webBase = 'https://www.sussytoons.wtf'
    
    def getManga(self, link: str) -> Manga:
        match = re.search(r'/obra/(\d+)', link)
        id_value = match.group(1)
        response = Http.get(f'{self.base}/obras/{id_value}').json()
        title = response['resultado']['obr_nome']
        return Manga(link, title)

    def getChapters(self, id: str) -> List[Chapter]:
        try:
            match = re.search(r'/obra/(\d+)', id)
            id_value = match.group(1)
            response = Http.get(f'{self.base}/obras/{id_value}').json()
            title = response['resultado']['obr_nome']
            chapters = []
            for ch in response['resultado']['capitulos']:
                chapters.append(Chapter(str(ch['cap_id']), ch['cap_nome'], title))
            return chapters
        except Exception as e:
            print(e)


    def getPages(self, ch: Chapter) -> Pages:
        cap_id = None
        if isinstance(ch.id, (list, tuple)) and ch.id:
            cap_id = ch.id[1] if len(ch.id) > 1 else ch.id[0]
        else:
            cap_id = ch.id

        if cap_id is None:
            raise ValueError('Identificador de capítulo inválido')

        cap_id = str(cap_id).strip()
        if not cap_id:
            raise ValueError('Identificador de capítulo inválido')

        response = Http.get(f'{self.base}/capitulos/{cap_id}')
        data = response.json().get('resultado', {})

        paginas = data.get('cap_paginas') or []
        if not paginas:
            raise RuntimeError('Nenhuma página disponível para este capítulo')

        images = []
        cdn_base = self.CDN.rstrip('/')

        def _format_wp_path(src_value: str) -> str:
            cleaned = src_value.lstrip('/')
            if cleaned.startswith('manga_'):
                return f'wp-content/uploads/WP-manga/data/{cleaned}'
            if cleaned.startswith('uploads/'):
                return f'wp-content/{cleaned}'
            if cleaned.startswith('WP-manga'):
                return f'wp-content/uploads/{cleaned}'
            if cleaned.startswith('wp-content/'):
                return cleaned
            return cleaned

        for pagina in paginas:
            path = (pagina.get('path') or '').strip('/')
            src = pagina.get('src') or ''
            if not src:
                continue

            if src.startswith('http'):  # already absolute
                images.append(src)
                continue

            if any(src.startswith(prefix) for prefix in ('manga_', 'uploads/', 'WP-manga', 'wp-content/')):
                normalized = _format_wp_path(src)
                images.append(f'{cdn_base}/{normalized}')
                continue

            normalized_path = posixpath.join(path, src.lstrip('/')) if path else src.lstrip('/')
            images.append(f'{cdn_base}/{normalized_path}')

        if not images:
            raise RuntimeError('Não foi possível construir as URLs das páginas do capítulo')

        return Pages(ch.id, ch.number, ch.name, images)

    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        effective_headers = {}
        if isinstance(headers, dict):
            effective_headers.update(headers)

        # CDN bloqueia requisições sem referer; mantemos user-agent padrão do cloudscraper
        effective_headers.setdefault('Referer', self.webBase)
        effective_headers.setdefault('Origin', self.webBase)
        effective_headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8')

        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=effective_headers,
            cookies=cookies
        )
