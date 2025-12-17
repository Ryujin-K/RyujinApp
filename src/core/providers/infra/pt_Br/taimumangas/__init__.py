import json
import re
from typing import List, Optional, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class TaimuMangasProvider(Base):
    name = 'Taimu Mangas'
    lang = 'pt-Br'
    domain = [
        'taimumangas.rzword.xyz',
    ]

    def __init__(self) -> None:
        self.url = 'https://taimumangas.rzword.xyz'
        self.cdn = 'https://api.taimumangas.com/media/'
        self.get_title = 'h1'
        self.chapter = 'a[href^="/reader/"]'

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
        title_el = soup.select_one(self.get_title)
        if title_el and title_el.get_text(strip=True):
            title = title_el.get_text().strip().replace('\n', ' ')
        else:
            title = (soup.title.get_text().strip() if soup.title else self.name)
        return Manga(link, title)
    
    def getChapters(self, id: str) -> List[Chapter]:
        all_chapters: List[Chapter] = []
        page = 1
        title: Optional[str] = None

        seen_codes = set()

        while True:
            url = f"{id}&page={page}" if '?' in id else f"{id}?page={page}"
            response = Http.get(url)
            html = response.data

            if page == 1:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_el = soup.select_one(self.get_title)
                title = title_el.get_text().strip().replace('\n', ' ') if title_el else self.name

            data = self._extract_json_block(html, '\\"chapters\\":{', '{', '}')
            if not isinstance(data, dict):
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
                base_title = title or self.name

                all_chapters.append(Chapter(link, number_str, base_title))

            if not data.get('has_next'):
                break

            page += 1

        def chapter_sort_key(chapter: Chapter) -> float:
            match = re.search(r'(\d+(?:\.\d+)?)', str(chapter.number))
            return float(match.group(1)) if match else 0.0

        all_chapters.sort(key=chapter_sort_key)
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