from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.scraper_logger import ScraperLogger
import json

class YushukeTheme(Base):
    def __init__(self) -> None:
        self.url = None
        self.chapters_api = f'{self.url}/ajax/lzmvke.php?'
        
        self.title = 'div.manga-title-row h1'
        self.manga_id_selector = "button#CarregarCapitulos"
        self.chapter_item_selector = 'a.chapter-item'
        self.chapter_number_selector = 'span.capitulo-numero'
        self.chapter_views_selector = 'span.chapter-views'
        self.pages_selector = "div.select-nav + * picture"
        self.id_manga = 'data-page'
        self.image_selector = "img"
        
        super().__init__()  # Chama o init da base que já faz o log
        ScraperLogger.debug(self.name, "init", "YushukeTheme configurado", 
                           selectors={
                               "title": self.title,
                               "manga_id": self.manga_id_selector,
                               "chapter_item": self.chapter_item_selector,
                               "chapter_number": self.chapter_number_selector,
                               "pages": self.pages_selector,
                               "image": self.image_selector
                           },
                           api_base=self.chapters_api)

    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Iniciando busca de manga", url=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one('div.manga-title-row h1')
            ScraperLogger.parsing(self.name, "div.manga-title-row h1", 1 if title else 0, 1)
            
            if not title:
                ScraperLogger.error(self.name, "getManga", "Título não encontrado")
                raise ValueError("Título do manga não encontrado")
            
            title_text = title.get_text(strip=True)
            ScraperLogger.success(self.name, "getManga", "Manga encontrado", 
                                title=title_text, manga_id=link)
            return Manga(link, title_text)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getManga", "Falha ao buscar manga", 
                              exception=e, url=link)
            raise

    def getChapters(self, id: str) -> List[Chapter]:
        ScraperLogger.info(self.name, "getChapters", "Iniciando busca de capítulos", manga_id=id)
        
        try:
            response = Http.get(id)
            ScraperLogger.http_request(self.name, "GET", id, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one(self.title)
            
            if not title:
                ScraperLogger.warning(self.name, "getChapters", "Título não encontrado, usando ID como fallback")
                title_text = id
            else:
                title_text = title.get_text(strip=True)
                ScraperLogger.debug(self.name, "getChapters", "Título extraído", title=title_text)
            
            chapter_list = []
            
            # Verificar se existe botão para API
            id_manga = soup.select_one(self.manga_id_selector)
            ScraperLogger.parsing(self.name, self.manga_id_selector, 1 if id_manga else 0, 0,
                                context="botão de carregamento de capítulos")
            
            if not id_manga:
                ScraperLogger.info(self.name, "getChapters", "API não disponível, usando método de fallback")
                
                # Fallback: Extrair capítulos diretamente da página
                get_chapters = soup.select(self.chapter_item_selector)
                ScraperLogger.parsing(self.name, self.chapter_item_selector, len(get_chapters), 1,
                                    context="capítulos diretos da página")
                
                for i, ch in enumerate(get_chapters):
                    try:
                        number_element = ch.select_one(self.chapter_number_selector)
                        if not number_element:
                            ScraperLogger.warning(self.name, "getChapters", 
                                                f"Número não encontrado no capítulo {i+1}")
                            continue
                        
                        # Remover elemento de views se existir
                        views_span = number_element.select_one(self.chapter_views_selector)
                        if views_span:
                            views_span.decompose()
                        
                        chapter_text = number_element.get_text(strip=True)
                        chapter_number = ' '.join(chapter_text.split()[:2])
                        
                        chapter_url = ch.get('href')
                        if not chapter_url.startswith('http'):
                            chapter_url = f'{self.url}{chapter_url}'
                        
                        chapter_list.append(Chapter(chapter_url, chapter_number, title_text))
                        
                        if i < 3:  # Log apenas os primeiros 3
                            ScraperLogger.debug(self.name, "getChapters", 
                                              f"Capítulo {i+1} processado (fallback)", 
                                              number=chapter_number, url=chapter_url[:50] + "...")
                                              
                    except Exception as ch_error:
                        ScraperLogger.warning(self.name, "getChapters", 

                                            f"Failed to process chapter {i+1} (fallback)", 
                                            error=str(ch_error))
                
                ScraperLogger.success(self.name, "getChapters", "Chapters loaded (fallback)", 
                                    total=len(chapter_list))
                return chapter_list
            
            # API method
            manga_id = id_manga.get(self.id_manga)
            ScraperLogger.info(self.name, "getChapters", "Using API to fetch chapters", 
                             manga_id=manga_id)
            
            current_page = 1
            
            while True:
                api_url = f'{self.chapters_api}manga_id={manga_id}&page={current_page}&order=DESC'
                ScraperLogger.debug(self.name, "getChapters", f"Fetching API page {current_page}", 
                                  api_url=api_url)
                
                response = Http.get(api_url)
                ScraperLogger.http_request(self.name, "GET", api_url, response.status)
                
                try:
                    data = json.loads(response.content)
                    ScraperLogger.debug(self.name, "getChapters", "API response decoded", 
                                      page=current_page, 
                                      has_chapters=bool(data.get('chapters')))
                    
                    if not data.get('chapters'):
                        ScraperLogger.info(self.name, "getChapters", f"Page {current_page} empty, finishing")
                        break
                    
                    chapters_html = BeautifulSoup(data['chapters'], 'html.parser')
                    get_chapters = chapters_html.select(self.chapter_item_selector)
                    ScraperLogger.parsing(self.name, self.chapter_item_selector, len(get_chapters), 0,
                                        context=f"API chapters page {current_page}")
                    
                    if not get_chapters:
                        ScraperLogger.info(self.name, "getChapters", f"No chapters found on page {current_page}")
                        break
                        
                    for i, ch in enumerate(get_chapters):
                        try:
                            number_element = ch.select_one(self.chapter_number_selector)
                            if not number_element:
                                ScraperLogger.warning(self.name, "getChapters", 
                                                    f"Number not found in API chapter")
                                continue
                            
                            # Remove views element if exists
                            views_span = number_element.select_one(self.chapter_views_selector)
                            if views_span:
                                views_span.decompose()
                            
                            chapter_text = number_element.get_text(strip=True)
                            chapter_number = ' '.join(chapter_text.split()[:2])
                            
                            chapter_url = ch.get('href')
                            if not chapter_url.startswith('http'):
                                chapter_url = f'{self.url}{chapter_url}'
                                
                            chapter_list.append(Chapter(chapter_url, chapter_number, title_text))
                            
                            # Log only the first chapters of each page
                            if i < 2:
                                ScraperLogger.debug(self.name, "getChapters", 
                                                  f"API chapter processed", 
                                                  page=current_page, number=chapter_number, 
                                                  url=chapter_url[:50] + "...")
                                                  
                        except Exception as ch_error:
                            ScraperLogger.warning(self.name, "getChapters", 
                                                f"Failed to process API chapter", 
                                                page=current_page, error=str(ch_error))
                    
                    ScraperLogger.debug(self.name, "getChapters", f"Page {current_page} processed", 
                                      chapters_found=len(get_chapters), 
                                      total_chapters=len(chapter_list))
                    current_page += 1
                    
                except json.JSONDecodeError as json_error:
                    ScraperLogger.error(self.name, "getChapters", "Error decoding API JSON", 
                                      exception=json_error, page=current_page)
                    break
                    
            ScraperLogger.success(self.name, "getChapters", "Chapters loaded via API", 
                                total=len(chapter_list), pages_processed=current_page-1)
            return chapter_list
            
        except Exception as e:
            ScraperLogger.error(self.name, "getChapters", "Failed to fetch chapters", 
                              exception=e, manga_id=id)
            raise

    def getPages(self, ch: Chapter) -> Pages:
        ScraperLogger.info(self.name, "getPages", "Starting page search", 
                         chapter=ch.number, chapter_id=ch.id)
        
        try:
            response = Http.get(ch.id)
            ScraperLogger.http_request(self.name, "GET", ch.id, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find picture elements
            picture_elements = soup.select(self.pages_selector)
            ScraperLogger.parsing(self.name, self.pages_selector, len(picture_elements), 1,
                                context="picture elements")
            
            images = []
            for index, picture_element in enumerate(picture_elements):
                try:
                    img_element = picture_element.select_one(self.image_selector)
                    if not img_element:
                        ScraperLogger.warning(self.name, "getPages", 
                                            f"img element not found in picture {index+1}")
                        continue
                    
                    image_url = img_element.get('src')
                    if not image_url or not image_url.strip():
                        ScraperLogger.warning(self.name, "getPages", 
                                            f"Image URL {index+1} empty or invalid")
                        continue
                    
                    # Build full URL if needed
                    if not image_url.startswith('http'):
                        image_url = f"{self.url}{image_url}"
                    
                    images.append(image_url)
                    
                    if index < 3:  # Log only the first 3 images
                        ScraperLogger.debug(self.name, "getPages", 
                                          f"Image {index+1} processed", 
                                          src=image_url[:50] + "...")
                        
                except Exception as img_error:
                    ScraperLogger.warning(self.name, "getPages", 
                                        f"Failed to process image {index+1}", 
                                        error=str(img_error))
            
            ScraperLogger.success(self.name, "getPages", "Pages loaded", 
                                total=len(images), chapter=ch.number)
            return Pages(ch.id, ch.number, ch.name, images)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getPages", "Failed to fetch pages", 
                              exception=e, chapter=ch.number)
            raise

