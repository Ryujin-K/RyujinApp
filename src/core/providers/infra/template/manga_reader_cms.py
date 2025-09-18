import base64
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from urllib.parse import unquote, urljoin, urlparse
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.scraper_logger import ScraperLogger

class MangaReaderCms(Base):
    def __init__(self):
        super().__init__()  # Calls the base init which already logs
        self.url = None
        self.path = '/'

        self.query_mangas = 'ul.manga-list li a'
        self.query_chapters = 'ul.chapters li h5.chapter-title-rtl'
        self.query_pages = 'div#all source.img-responsive'
        self.query_title_for_uri = 'h1.entry-title'
        
        ScraperLogger.debug(self.name, "init", "MangaReaderCms configured", 
                           selectors={
                               "mangas": self.query_mangas,
                               "chapters": self.query_chapters,
                               "pages": self.query_pages,
                               "title": self.query_title_for_uri
                           })

    def fetch_dom(self, response, query):
        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.select(query)
        ScraperLogger.parsing(self.name, query, len(elements), 0, context="fetch_dom")
        return elements

    def get_relative_link(self, element):
        return element['href']

    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Starting manga search", url=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            uri = urlparse(link)
            id = uri.path + '?' + uri.query if uri.query else uri.path
            ScraperLogger.debug(self.name, "getManga", "ID extracted from URL", manga_id=id)
            
            data = self.fetch_dom(response, self.query_title_for_uri)
            if not data:
                ScraperLogger.error(self.name, "getManga", "Title not found")
                raise ValueError("Manga title not found")
            
            title = data[0].text.strip()
            ScraperLogger.success(self.name, "getManga", "Manga found", 
                                title=title, manga_id=id)
            return Manga(id=id, name=title)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getManga", "Failed to fetch manga", 
                              exception=e, url=link)
            raise

    def getChapters(self, id: str) -> List[Chapter]:
        ScraperLogger.info(self.name, "getChapters", "Starting chapter search", manga_id=id)
        
        try:
            full_url = urljoin(self.url, id)
            ScraperLogger.debug(self.name, "getChapters", "Full URL built", url=full_url)
            
            response = Http.get(full_url)
            ScraperLogger.http_request(self.name, "GET", full_url, response.status)
            
            # Fetch chapters
            data = self.fetch_dom(response, self.query_chapters)
            if not data:
                ScraperLogger.error(self.name, "getChapters", "No chapters found")
                raise ValueError("No chapters found")
            
            # Fetch title
            title_elements = self.fetch_dom(response, self.query_title_for_uri)
            if not title_elements:
                ScraperLogger.warning(self.name, "getChapters", "Title not found, using ID")
                title = id
            else:
                title = title_elements[0].text.strip()
                ScraperLogger.debug(self.name, "getChapters", "Title extracted", title=title)
            
            chapters = []
            for i, element in enumerate(data):
                try:
                    anchor = element if element.name == 'a' else element.select_one('a')
                    if not anchor:
                        ScraperLogger.warning(self.name, "getChapters", 
                                            f"Anchor not found in chapter {i+1}")
                        continue
                    
                    # Fetch chapter number
                    number_elements = element.select('span.chapternum')
                    if not number_elements:
                        ScraperLogger.warning(self.name, "getChapters", 
                                            f"Number not found in chapter {i+1}")
                        chapter_number = f"Chapter {i+1}"
                    else:
                        chapter_number = number_elements[0].text
                    
                    chapter_id = self.get_relative_link(anchor)
                    chapters.append(Chapter(id=chapter_id, number=chapter_number, name=title))
                    
                    if i < 3:  # Log only the first 3
                        ScraperLogger.debug(self.name, "getChapters", 
                                          f"Chapter {i+1} processed", 
                                          number=chapter_number, ch_id=chapter_id[:50] + "...")
                        
                except Exception as ch_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        f"Failed to process chapter {i+1}", 
                                        error=str(ch_error))
            
            chapters.reverse()
            ScraperLogger.success(self.name, "getChapters", "Chapters loaded", 
                                total=len(chapters), manga_title=title)
            return chapters
            
        except Exception as e:
            ScraperLogger.error(self.name, "getChapters", "Failed to fetch chapters", 
                              exception=e, manga_id=id)
            raise

    def getPages(self, ch: Chapter) -> Pages:
        ScraperLogger.info(self.name, "getPages", "Starting to fetch pages", 
                         chapter=ch.number, chapter_id=ch.id)
        
        try:
            full_url = urljoin(self.url, ch.id)
            ScraperLogger.debug(self.name, "getPages", "Full URL built", url=full_url)
            
            response = Http.get(full_url)
            ScraperLogger.http_request(self.name, "GET", full_url, response.status)
            
            data = self.fetch_dom(response, self.query_pages)
            if not data:
                ScraperLogger.error(self.name, "getPages", "No pages found")
                raise ValueError("No pages found")
            
            pages = []
            for i, element in enumerate(data):
                try:
                    # Try base64 decoding method first
                    data_src = element.get('data-src')
                    if data_src:
                        try:
                            src = data_src.split('://').pop()
                            decoded_url = unquote(base64.b64decode(src or '').decode('utf-8'))
                            pages.append(decoded_url)
                            
                            if i < 3:  # Log only the first 3
                                ScraperLogger.debug(self.name, "getPages", 
                                                  f"Page {i+1} decoded (base64)", 
                                                  url=decoded_url[:50] + "...")
                        except Exception as decode_error:
                            ScraperLogger.debug(self.name, "getPages", 
                                              f"Failed to decode base64 for page {i+1}, using fallback", 
                                              error=str(decode_error))
                            # Fallback: use src directly
                            src = (element.get('data-src') or element.get('src', '')).strip()
                            if src:
                                full_src = urljoin(response.url, src)
                                pages.append(full_src)
                                
                                if i < 3:
                                    ScraperLogger.debug(self.name, "getPages", 
                                                      f"Page {i+1} processed (fallback)", 
                                                      url=full_src[:50] + "...")
                    else:
                        # Use src if data-src does not exist
                        src = element.get('src', '').strip()
                        if src:
                            full_src = urljoin(response.url, src)
                            pages.append(full_src)
                            
                            if i < 3:
                                ScraperLogger.debug(self.name, "getPages", 
                                                  f"Page {i+1} processed (src)", 
                                                  url=full_src[:50] + "...")
                        
                except Exception as page_error:
                    ScraperLogger.warning(self.name, "getPages", 
                                        f"Failed to process page {i+1}", 
                                        error=str(page_error))
            
            ScraperLogger.success(self.name, "getPages", "Pages loaded", 
                                total=len(pages), chapter=ch.number)
            return Pages(id=ch.id, number=ch.number, name=ch.name, pages=pages)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getPages", "Failed to fetch pages", 
                              exception=e, chapter=ch.number)
            raise