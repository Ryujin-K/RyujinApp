from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.scraper_logger import ScraperLogger

class BloggerCms(Base):

    def __init__(self) -> None:
        self.get_title = 'header h1'
        self.API_domain = 'www.strellascan.xyz'
        self.get_pages = 'div.separator a img'
        
        super().__init__()  # Calls the base init which already logs
        ScraperLogger.debug(self.name, "init", "BloggerCms configured", 
                           api_domain=self.API_domain,
                           selectors={
                               "title": self.get_title,
                               "pages": self.get_pages
                           })
    
    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Starting manga search", url=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one(self.get_title)
            ScraperLogger.parsing(self.name, self.get_title, 1 if title else 0, 1)
            
            if not title:
                ScraperLogger.error(self.name, "getManga", "Title not found")
                raise ValueError("Manga title not found")
            
            title_text = title.get_text(strip=True)
            ScraperLogger.success(self.name, "getManga", "Manga found", 
                                title=title_text, manga_id=link)
            return Manga(link, title_text)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getManga", "Failed to fetch manga", 
                              exception=e, url=link)
            raise

    def getChapters(self, id: str) -> List[Chapter]:
        ScraperLogger.info(self.name, "getChapters", "Starting chapter search", manga_id=id)
        
        try:
            response = Http.get(id)
            ScraperLogger.http_request(self.name, "GET", id, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one(self.get_title)
            
            if not title:
                ScraperLogger.error(self.name, "getChapters", "Title not found")
                raise ValueError("Manga title not found")
            
            title_text = title.get_text(strip=True)
            ScraperLogger.debug(self.name, "getChapters", "Title extracted", title=title_text)
            
            # Fetch chapters via API
            api_url = f'https://{self.API_domain}/feeds/posts/default/-/{title_text}?alt=json&start-index=1&max-results=150'
            ScraperLogger.info(self.name, "getChapters", "Fetching chapters via API", api_url=api_url)
            
            response = Http.get(api_url)
            ScraperLogger.http_request(self.name, "GET", api_url, response.status)
            
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            ScraperLogger.parsing(self.name, "API entries", len(entries), 1, 
                                context="API chapters")
            
            chapters_list = []
            for i, ch in enumerate(entries):
                try:
                    ch_url = ch['link'][4]['href']
                    if ch_url == id:  # Skip the manga's own page
                        continue
                    
                    ch_title = ch['title']['$t']
                    chapters_list.append(Chapter(ch_url, ch_title, title_text))
                    
                    if i < 3:  # Log only the first 3
                        ScraperLogger.debug(self.name, "getChapters", 
                                          f"Chapter {len(chapters_list)} processed", 
                                          title=ch_title, url=ch_url[:50] + "...")
                except Exception as ch_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        f"Failed to process chapter {i+1}", 
                                        error=str(ch_error))
            
            ScraperLogger.success(self.name, "getChapters", "Chapters loaded via API", 
                                total=len(chapters_list), manga_title=title_text)
            return chapters_list
            
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
            get_images = soup.select(self.get_pages)
            ScraperLogger.parsing(self.name, self.get_pages, len(get_images), 1, 
                                context="chapter images")
            
            images_list = []
            for i, img in enumerate(get_images):
                try:
                    img_src = img.get('src')
                    if img_src:
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