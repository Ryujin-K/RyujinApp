import re
import json
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Chapter, Pages
from core.providers.infra.template.wordpress_madara import WordPressMadara

class NexusScanProvider(WordPressMadara):
    name = 'Nexus Scan'
    lang = 'pt-Br'
    domain = ['nexusscan.site']

    def __init__(self):
        self.url = 'https://nexusscan.site/'

        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'h1.item-title'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        self.api_chapters = 'https://nexusscan.site/api/'


    def getChapters(self, id: str) -> List[Chapter]:
        uri = urljoin(self.url, id)
        response = Http.get(uri, timeout=getattr(self, 'timeout', None))
        soup = BeautifulSoup(response.content, 'html.parser')
        data = soup.select(self.query_title_for_uri)
        element = data.pop()
        title = element['content'].strip() if 'content' in element.attrs else element.text.strip()

        try:
            data = self._get_chapters_ajax(id)
        except Exception:
            raise Exception("erro ajax")

        chs = []
        for el in data:
            ch_id = el.get("href", "").strip()
            ch_number = el.get("data-chapter-number", "").strip()
            chars_to_remove = ['"', '\\n', '\\', '\r', '\t', "'"]
            for char in chars_to_remove:
                ch_number = ch_number.replace(char, "")
                ch_id = ch_id.replace(char, "")
            chs.append(Chapter(ch_id, ch_number, title))

        chs.reverse()
        return chs
    
    def getPages(self, ch: Chapter) -> Pages:
        uri = str(ch.id)
        if uri.startswith("/manga/"):
            uri = uri.replace("/manga/", "page-data/", 1)
        elif uri.startswith("manga/"):
            uri = uri.replace("manga/", "page-data/", 1)
        else:
            print(f"Padrão inesperado em ch.id: {uri}")
            parts = uri.strip('/').split('/')
            if len(parts) >= 2:
                uri = f"page-data/{'/'.join(parts[1:])}" 
        
        uri_base = f"{self.api_chapters}{uri}"
        count = 1
        list = [] 
        while True:
            uri = f"{uri_base}{count}/"
            try:
                response = Http.get(uri)
                soup = BeautifulSoup(response.content, 'html.parser')
                temp = soup.text
                image = dict(json.loads(temp)).get("image_url")
                list.append(image)
                count += 1
            except:
                break

        number = re.findall(r'\d+\.?\d*', str(ch.number))[0]
        return Pages(ch.id, number, ch.name, list)
    
    def _get_chapters_ajax(self, manga_id):
        title = manga_id.split('/')[-2]
        page = 1
        all_chapters = []
        seen_hrefs = set()
        
        while True:
            uri = f'https://nexusscan.site/ajax/load-chapters/?item_slug={title}&page={page}&sort=desc&q='
            response = Http.get(uri, timeout=getattr(self, 'timeout', None))
                
            data = self._fetch_dom(response, self.query_chapters)
            
            if not data:
                break
            
            page_hrefs = set()
            repeated_count = 0
            
            for chapter in data:
                href = chapter.get("href", "")
                if href in seen_hrefs:
                    repeated_count += 1
                else:
                    seen_hrefs.add(href)
                    page_hrefs.add(href)
            
            if repeated_count >= len(data) * 0.5:
                break
            
            new_chapters = [ch for ch in data if ch.get("href", "") in page_hrefs]
            all_chapters.extend(new_chapters)
            
            page += 1
            
            if page > 100:
                break
        
        if all_chapters:
            return all_chapters
        else:
            raise Exception('No chapters found (ajax pagination)!')