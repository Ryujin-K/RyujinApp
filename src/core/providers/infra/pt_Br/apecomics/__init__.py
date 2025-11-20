from core.providers.infra.template.wordpress_etoshore_manga_theme import WordpressEtoshoreMangaTheme
from typing import List
from core.__seedwork.infra.http import Http
from bs4 import BeautifulSoup
from core.providers.domain.entities import Chapter, Manga, Pages
import re
import json
import html

class ApeComicsProvider(WordpressEtoshoreMangaTheme):
    name = 'Ape Comics'
    lang = 'pt_Br'
    domain = ['apecomics.net']

    def __init__(self) -> None:
        self.get_title = 'h1'
        self.get_chapters_list = 'div.eplister#chapterlist > ul'
        self.chapter = 'li a'
        self.get_chapter_number = 'span.chapternum'
        self.get_div_page = 'div#readerarea'
        self.get_pages = 'img'
    
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
        soup = BeautifulSoup(response.content, 'html.parser')
        
        scripts = soup.find_all('script')
        images_list = []
        
        for script in scripts:
            if script.string and 'ts_reader.run' in script.string:

                match = re.search(r'ts_reader\.run\((.*?)\);', script.string, re.DOTALL)
                if match:
                    try:

                        json_str = match.group(1)
                        data = json.loads(json_str)
                        
                        if 'sources' in data and len(data['sources']) > 0:
                            if 'images' in data['sources'][0]:
                                for img_url in data['sources'][0]['images']:

                                    decoded_url = html.unescape(img_url)
                                    images_list.append(decoded_url)
                                break
                    except json.JSONDecodeError:
                        pass
        
        if not images_list:
            images = soup.select_one(self.get_div_page)
            if images:
                image = images.select(self.get_pages)
                for img in image:
                    images_list.append(img.get('src'))
        
        return Pages(ch.id, ch.number, ch.name, images_list)
