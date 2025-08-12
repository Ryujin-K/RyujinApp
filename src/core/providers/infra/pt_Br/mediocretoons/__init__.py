from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class MediocreToonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt-Br'
    domain = ['mediocretoons.com']

    def __init__(self) -> None:
        pass
    
    def getManga(self, link: str) -> Manga:
        response = Http.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.select_one('h1.text-lg').get_text(strip=True)
        
        return Manga(link, title)

    def getChapters(self, manga_url: str) -> List[Chapter]:
        response = Http.get(manga_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        chapters = []
        chapter_elements = soup.select('div.grow.flex.gap-5 span')  # Seleciona os números dos capítulos
        
        for idx, ch in enumerate(chapter_elements, start=1):
            chapter_number = ch.get_text(strip=True)
            chapter_url = f"{manga_url}/capitulos/{chapter_number}"  # Constrói a URL do capítulo
            chapters.append(Chapter(chapter_url, f"Capítulo {chapter_number}", ""))
        
        return chapters

    def getPages(self, chapter: Chapter) -> Pages:
        response = Http.get(chapter.id)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pages = []
        # Seleciona todas as divs que contêm as imagens das páginas
        page_containers = soup.select('div[style*="background: transparent"]')
        
        for container in page_containers:
            img = container.select_one('img')
            if img and img.get('src') and not img['src'].endswith('banner-comeco.JPG') and not img['src'].endswith('banner-fim.JPG'):
                pages.append(img['src'])
        
        return Pages(chapter.id, chapter.number, chapter.name, pages)