import re
from typing import Any, Dict, List
from urllib.parse import unquote, urlparse
from core.__seedwork.infra.http import Http
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class SussyToonsProvider(Base):
    name = 'Sussy Toons'
    lang = 'pt_Br'
    domain = ['new.sussytoons.site', 'www.sussyscan.com', 'www.sussytoons.site', 'www.sussytoons.wtf', 'sussytoons.wtf']

    def __init__(self) -> None:
        self.base = 'https://api2.sussytoons.wtf'
        self.CDN = 'https://cdn.sussytoons.wtf'
        self.webBase = 'https://www.sussytoons.wtf'
        self._manga_cache: Dict[str, Dict[str, Any]] = {}
        self._download_timeout = 60
    
    def getManga(self, link: str) -> Manga:
        identifier = self._extract_identifier(link)
        data = self._fetch_manga(identifier)
        title = data.get('obr_nome') or identifier
        return Manga(link, title)

    def getChapters(self, id: str) -> List[Chapter]:
        identifier = self._extract_identifier(id)
        data = self._fetch_manga(identifier)
        obra_id = data.get('obr_id')
        if not obra_id:
            raise RuntimeError('Não foi possível determinar o identificador da obra')

        chapters_data = self._fetch_chapters(obra_id)
        if not chapters_data:
            chapters_data = list(data.get('capitulos') or [])

        def sort_key(item: Dict[str, Any]):
            numero = item.get('cap_numero')
            cap_id = item.get('cap_id', 0)
            if isinstance(numero, (int, float)):
                return (float(numero), cap_id)
            if isinstance(numero, str):
                normalized = numero.replace(',', '.').strip()
                try:
                    return (float(normalized), cap_id)
                except ValueError:
                    pass
            return (float('inf'), cap_id)

        ordered = sorted(chapters_data, key=sort_key)
        chapters: List[Chapter] = []
        manga_title = data.get('obr_nome') or ''
        for chapter in ordered:
            cap_id = chapter.get('cap_id')
            if not cap_id:
                continue
            chapter_label = chapter.get('cap_nome') or str(chapter.get('cap_numero') or cap_id)
            chapters.append(Chapter(str(cap_id), str(chapter_label), manga_title))

        return chapters


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
        payload = response.json()
        if isinstance(payload, dict) and 'resultado' in payload:
            data = payload.get('resultado') or {}
        else:
            data = payload if isinstance(payload, dict) else {}

        paginas = data.get('cap_paginas') or []
        if not paginas:
            raise RuntimeError('Nenhuma página disponível para este capítulo')

        images = []
        cdn_base = self.CDN.rstrip('/')

        for pagina in paginas:
            path = (pagina.get('path') or '').strip()
            src = (pagina.get('src') or '').strip()
            
            if not src:
                continue

            if src.startswith('http://') or src.startswith('https://'):
                images.append(src)
                continue

            path_clean = path.lstrip('/')
            src_clean = src.lstrip('/')
            
            if path_clean and src_clean:
                full_url = f'{cdn_base}/{path_clean}/{src_clean}'
            elif src_clean:
                full_url = f'{cdn_base}/{src_clean}'
            else:
                continue
            
            images.append(full_url)

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
            cookies=cookies,
            timeout=self._download_timeout
        )

    def _extract_identifier(self, link: str) -> str:
        if not link:
            raise ValueError('Link de obra inválido')

        parsed = urlparse(link)
        segments = [segment for segment in parsed.path.split('/') if segment]
        identifier = None

        try:
            idx = segments.index('obra')
            identifier = segments[idx + 1]
        except (ValueError, IndexError):
            match = re.search(r'/obra/([^/?#]+)', link)
            if match:
                identifier = match.group(1)

        if not identifier:
            raise ValueError('Identificador de obra não encontrado no link informado')

        identifier = unquote(identifier).strip()
        if not identifier:
            raise ValueError('Identificador de obra inválido')

        return identifier

    def _fetch_manga(self, identifier: str) -> Dict[str, Any]:
        cache_key = identifier.lower()
        if cache_key not in self._manga_cache:
            response = Http.get(f'{self.base}/obras/{identifier}')
            if response.status != 200:
                raise RuntimeError('Falha ao buscar dados da obra')

            data = response.json()
            if isinstance(data, dict) and data.get('statusCode'):
                message = data.get('message') or 'Obra não encontrada'
                raise RuntimeError(message)

            self._manga_cache[cache_key] = data

        return self._manga_cache[cache_key]

    def _fetch_chapters(self, obra_id: int) -> List[Dict[str, Any]]:
        chapters: List[Dict[str, Any]] = []
        page = 1
        page_size = 100

        while True:
            params = {
                'obr_id': obra_id,
                'pagina': page,
                'limite': page_size
            }
            response = Http.get(f'{self.base}/capitulos', params=params)
            if response.status != 200:
                break

            payload = response.json()
            if not isinstance(payload, dict):
                break

            items = payload.get('capitulos') or []
            if not items:
                break

            chapters.extend(items)

            has_next = payload.get('hasNextPage')
            total_pages = payload.get('totalPaginas')
            total_items = payload.get('total')

            if has_next:
                page += 1
                continue

            if isinstance(total_pages, int) and page < total_pages:
                page += 1
                continue

            if isinstance(total_items, int) and len(chapters) < total_items:
                page += 1
                continue

            if len(items) >= page_size:
                page += 1
                continue

            break

        return chapters
