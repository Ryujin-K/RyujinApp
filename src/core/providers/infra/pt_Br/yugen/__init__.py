import json
from typing import List, Optional, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class YugenProvider(Base):
    name = 'Yugen mangas'
    lang = 'pt-Br'
    domain = [
        'yugenmangasbr.dxtg.online',
        'yugenmangasbr.yocat.xyz',
    ]

    def __init__(self) -> None:
        self.url = 'https://yugenmangasbr.dxtg.online'
        self.cdn = 'https://api.yugenweb.com/media/'
        self.get_title = 'h1'
        self.get_chapters_list = 'div.grid.gap-2'
        self.chapter = 'a[href^="/reader/"]'
        self.get_chapter_number = 'p.font-semibold'

    def _extract_json_block(self, source: str, marker: str, opener: str, closer: str) -> Optional[Any]:
        idx = source.find(marker)
        if idx == -1:
            return None

        start = idx + len(marker)
        depth = 1
        in_string = False
        escape = False
        buffer = [opener]

        for ch in source[start:]:
            buffer.append(ch)

            if escape:
                escape = False
                continue

            if ch == '\\':
                escape = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if not in_string:
                if ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        break

        raw_json = ''.join(buffer)
        try:
            return json.loads(bytes(raw_json, 'utf-8').decode('unicode_escape'))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _sort_number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def getManga(self, link: str) -> Manga:
        response = Http.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.select_one(self.get_title)
        return Manga(link, title.get_text().strip().replace('\n', ' '))
    
    def getChapters(self, id: str) -> List[Chapter]:
        all_chapters = []
        page = 1
        title = None
        
        seen_codes = set()

        while True:
            url = f"{id}&page={page}" if '?' in id else f"{id}?page={page}"
            response = Http.get(url)
            html = response.data

            if page == 1:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_element = soup.select_one(self.get_title)
                if title_element:
                    title = title_element.get_text().strip().replace('\n', ' ')

            data = self._extract_json_block(html, '\\"chapters\\":{', '{', '}')
            if not data:
                break

            chapters = data.get('chapters') or []
            if not chapters:
                break

            for chapter in chapters:
                code = chapter.get('code')
                number = chapter.get('number')
                if not code or code in seen_codes:
                    continue

                seen_codes.add(code)
                link = urljoin(self.url, f"/reader/{code}")
                number_str = str(number) if number is not None else ''
                base_title = title or chapter.get('title') or self.name

                all_chapters.append(Chapter(link, number_str, base_title))

            if not data.get('has_next'):
                break

            page += 1
        
        return all_chapters

    def getPages(self, ch: Chapter) -> Pages:
        response = Http.get(ch.id)
        html = response.data

        pages_data = self._extract_json_block(html, '\\"pages\\":[', '[', ']')
        if not pages_data:
            return Pages(ch.id, ch.number, ch.name, [])

        pages_data.sort(key=lambda item: self._sort_number(item.get('number')))

        links = []
        for page in pages_data:
            path = page.get('path')
            if not path:
                continue
            links.append(urljoin(self.cdn, path.lstrip('/')))

        return Pages(ch.id, ch.number, ch.name, links)