import re
import json
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class YugenProvider(Base):
    name = 'Yugen mangas'
    lang = 'pt-Br'
    domain = ['yugenmangasbr.yocat.xyz']

    def __init__(self) -> None:
        self.url = 'https://yugenmangasbr.yocat.xyz'
        self.cdn = 'https://api.yugenweb.com/media/'
        self.get_title = 'h1'
        self.get_chapters_list = 'div.grid.gap-2'
        self.chapter = 'a[href^="/reader/"]'
        self.get_chapter_number = 'p.font-semibold'

    def getManga(self, link: str) -> Manga:
        response = Http.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.select_one(self.get_title)
        return Manga(link, title.get_text().strip().replace('\n', ' '))
    
    def getChapters(self, id: str) -> List[Chapter]:
        all_chapters = []
        page = 1
        title = None
        
        while True:
            url = f"{id}&page={page}" if '?' in id else f"{id}?page={page}"
            response = Http.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if page == 1:
                title_element = soup.select_one(self.get_title)
                if title_element:
                    title = title_element.get_text().strip().replace('\n', ' ')
            
            chapters_list = soup.select_one(self.get_chapters_list)
            if not chapters_list:
                break
            
            chapters = chapters_list.select(self.chapter)
            if not chapters:
                break
            
            for ch in chapters:
                number_element = ch.select_one(self.get_chapter_number)
                if number_element:
                    link = urljoin(self.url, ch.get('href'))
                    all_chapters.append(Chapter(link, number_element.get_text().strip(), title))
            
            page += 1
        
        return all_chapters

    def getPages(self, ch: Chapter) -> Pages:
        response = Http.get(ch.id)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        scripts = soup.find_all('script')
        if scripts:
            last_script = scripts[-1]
            
            if last_script.string:
                script_content = last_script.string
                
                match = re.search(r'\\"pages\\":\[(\{[^\]]+\}(?:,\{[^\]]+\})*)\]', script_content)
                if match:
                    try:
                        json_str = '[' + match.group(1).replace('\\"', '"') + ']'
                        pages_json = json.loads(json_str)
                        
                        pages_json.sort(key=lambda x: x.get('number', 0))
                        
                        links = []
                        for page in pages_json:
                            path = page.get('path', '')
                            if path:
                                links.append(urljoin(self.cdn, path))
                        
                        if links:
                            return Pages(ch.id, ch.number, ch.name, links)
                    except json.JSONDecodeError:
                        pass
        
        return Pages(ch.id, ch.number, ch.name, [])