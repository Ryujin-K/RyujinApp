import re
import json
from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class PlumaComicsProvider(Base):
    name = 'Pluma Comics'
    lang = 'pt-Br'
    domain = ['plumacomics.cloud']

    def __init__(self) -> None:
        self.url = 'https://plumacomics.cloud'
        self.get_title = 'h1'
        self.get_chapters_list = 'div.eplister#chapterlist > ul'
        self.chapter = 'li a'
        self.get_chapter_number = 'span.chapternum'
        self.get_div_page = 'div#readerarea'
        self.get_pages = 'img.ts-main-image'

    def getManga(self, link: str) -> Manga:
        response = Http.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.select_one(self.get_title)
        return Manga(link, title.get_text().strip())

    def getChapters(self, id: str) -> List[Chapter]:
        response = Http.get(id)
        soup = BeautifulSoup(response.content, 'html.parser')
        chapters_list = soup.select_one(self.get_chapters_list)
        chapter = chapters_list.select(self.chapter)
        title = soup.select_one(self.get_title)
        list = []
        for ch in chapter:
            number = ch.select_one(self.get_chapter_number)
            list.append(Chapter(ch.get('href'), number.get_text().strip(), title.get_text().strip()))
        return list

    def getPages(self, ch: Chapter) -> Pages:
        response = Http.get(ch.id)
        html_content = response.content.decode('utf-8') if isinstance(response.content, bytes) else response.content
        
        # Procura pelo padrão ts_reader.run({...})
        pattern = r'ts_reader\.run\((\{.*?\})\);'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                
                # Extrai as imagens do primeiro source
                if 'sources' in data and len(data['sources']) > 0:
                    images = data['sources'][0].get('images', [])
                    if images:
                        return Pages(ch.id, ch.number, ch.name, images)
            except json.JSONDecodeError:
                pass
        
        # Fallback: extrai do HTML direto
        soup = BeautifulSoup(html_content, 'html.parser')
        div_pages = soup.select_one(self.get_div_page)
        
        if div_pages:
            images = div_pages.select(self.get_pages)
            img_urls = []
            for img in images:
                url = img.get('data-src') or img.get('src')
                if url and 'readerarea.svg' not in url:
                    img_urls.append(url)
            
            if img_urls:
                return Pages(ch.id, ch.number, ch.name, img_urls)
        
        return Pages(ch.id, ch.number, ch.name, [])