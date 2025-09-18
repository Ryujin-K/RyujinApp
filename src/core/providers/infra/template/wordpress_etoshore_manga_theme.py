from typing import List
from core.__seedwork.infra.http import Http
from bs4 import BeautifulSoup
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.scraper_logger import ScraperLogger

class WordpressEtoshoreMangaTheme(Base):

    def __init__(self) -> None:
        self.get_title = 'h1'
        self.get_chapters_list = 'div.list-box.chapter-list'
        self.chapter = 'li.language-BR > a'
        self.get_chapter_number = 'div.title'
        self.get_div_page = 'div.chapter-image-content'
        self.get_pages = 'noscript > img'
        
        super().__init__()  # Chama o init da base que já faz o log
        ScraperLogger.debug(self.name, "init", "WordpressEtoshoreMangaTheme configurado", 
                           selectors={
                               "title": self.get_title,
                               "chapters_list": self.get_chapters_list,
                               "chapter": self.chapter,
                               "chapter_number": self.get_chapter_number,
                               "pages_container": self.get_div_page,
                               "pages": self.get_pages
                           })
    
    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Iniciando busca de manga", url=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one(self.get_title)
            ScraperLogger.parsing(self.name, self.get_title, 1 if title else 0, 1)
            
            if not title:
                ScraperLogger.error(self.name, "getManga", "Título não encontrado", 
                                  selector=self.get_title)
                raise ValueError("Título do manga não encontrado")
            
            title_text = title.get_text().strip()
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
            
            # Verificar título
            title = soup.select_one(self.get_title)
            if not title:
                ScraperLogger.warning(self.name, "getChapters", "Título não encontrado, usando ID como fallback")
                title_text = id
            else:
                title_text = title.get_text().strip()
                ScraperLogger.debug(self.name, "getChapters", "Título extraído", title=title_text)
            
            # Buscar lista de capítulos
            chapters_list = soup.select_one(self.get_chapters_list)
            ScraperLogger.parsing(self.name, self.get_chapters_list, 1 if chapters_list else 0, 1,
                                context="container de capítulos")
            
            if not chapters_list:
                ScraperLogger.error(self.name, "getChapters", "Container de capítulos não encontrado",
                                  selector=self.get_chapters_list)
                raise ValueError("Container de capítulos não encontrado")
            
            # Buscar capítulos individuais
            chapter_elements = chapters_list.select(self.chapter)
            ScraperLogger.parsing(self.name, self.chapter, len(chapter_elements), 1,
                                context="capítulos em português")
            
            list = []
            for i, ch in enumerate(chapter_elements):
                try:
                    ch_url = ch.get('href')
                    if not ch_url:
                        ScraperLogger.warning(self.name, "getChapters", 
                                            f"URL não encontrada no capítulo {i+1}")
                        continue
                    
                    number_element = ch.select_one(self.get_chapter_number)
                    if not number_element:
                        ScraperLogger.warning(self.name, "getChapters", 
                                            f"Número não encontrado no capítulo {i+1}")
                        number_text = f"Capítulo {i+1}"
                    else:
                        number_text = number_element.get_text().strip()
                    
                    list.append(Chapter(ch_url, number_text, title_text))
                    
                    if i < 3:  # Log apenas os primeiros 3
                        ScraperLogger.debug(self.name, "getChapters", 
                                          f"Capítulo {i+1} processado", 
                                          number=number_text, url=ch_url[:50] + "...")
                        
                except Exception as ch_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        f"Falha ao processar capítulo {i+1}", 
                                        error=str(ch_error))
            
            ScraperLogger.success(self.name, "getChapters", "Capítulos carregados", 
                                total=len(list), manga_title=title_text)
            return list
            
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
            
            # Find image container
            images_container = soup.select_one(self.get_div_page)
            ScraperLogger.parsing(self.name, self.get_div_page, 1 if images_container else 0, 1,
                                context="image container")
            
            if not images_container:
                ScraperLogger.error(self.name, "getPages", "Image container not found",
                                  selector=self.get_div_page)
                raise ValueError("Image container not found")
            
            # Find individual images
            image_elements = images_container.select(self.get_pages)
            ScraperLogger.parsing(self.name, self.get_pages, len(image_elements), 1,
                                context="chapter images")
            
            images_list = []
            for i, img in enumerate(image_elements):
                try:
                    img_src = img.get('src')
                    if not img_src:
                        ScraperLogger.warning(self.name, "getPages", 
                                            f"Image URL {i+1} not found")
                        continue
                    
                    images_list.append(img_src)
                    
                    if i < 3:  # Log only the first 3 images
                        ScraperLogger.debug(self.name, "getPages", 
                                          f"Image {i+1} processed", 
                                          src=img_src[:50] + "...")
                        
                except Exception as img_error:
                    ScraperLogger.warning(self.name, "getPages", 
                                        f"Failed to process image {i+1}", 
                                        error=str(img_error))
            
            ScraperLogger.success(self.name, "getPages", "Pages loaded", 
                                total=len(images_list), chapter=ch.number)
            return Pages(ch.id, ch.number, ch.name, images_list)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getPages", "Failed to fetch pages", 
                              exception=e, chapter=ch.number)
            raise

