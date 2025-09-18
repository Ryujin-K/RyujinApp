import os
import re
import ast
import math
import pillow_avif
from PIL import Image
from io import BytesIO
from typing import List
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.config.img_conf import get_config
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.download.domain.download_entity import Chapter as DChapter
from core.__seedwork.infra.utils.sanitize_folder import sanitize_folder_name
from core.providers.infra.template.scraper_logger import ScraperLogger
Image.MAX_IMAGE_PIXELS = 933120000

class ScanMadaraClone(Base):

    def __init__(self):
        self.url = None
        super().__init__()  # Chama o init da base que já faz o log
        ScraperLogger.debug(self.name, "init", "ScanMadaraClone inicializado", 
                           img_max_pixels=Image.MAX_IMAGE_PIXELS)
    
    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Iniciando busca de manga", url=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tags = soup.find_all('h1', class_='desc__titulo__comic')
            ScraperLogger.parsing(self.name, "h1.desc__titulo__comic", len(tags), 1)
            
            if not tags:
                ScraperLogger.error(self.name, "getManga", "Título não encontrado")
                raise ValueError("Título do manga não encontrado")
            
            title = tags[0].get_text()
            ScraperLogger.success(self.name, "getManga", "Manga encontrado", 
                                title=title, manga_id=link)
            return Manga(id=link, name=title)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getManga", "Falha ao buscar manga", 
                              exception=e, url=link)
            raise

    def getChapters(self, link: str) -> List[Chapter]:
        ScraperLogger.info(self.name, "getChapters", "Iniciando busca de capítulos", manga_id=link)
        
        try:
            response = Http.get(link)
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tags = soup.find_all('a', class_='link__capitulos')
            ScraperLogger.parsing(self.name, "a.link__capitulos", len(tags), 1)
            
            title_tags = soup.find_all('h1', class_='desc__titulo__comic')
            if not title_tags:
                ScraperLogger.warning(self.name, "getChapters", "Título não encontrado, usando fallback")
                title = "Unknown"
            else:
                title = title_tags[0].get_text()
                ScraperLogger.debug(self.name, "getChapters", "Título extraído", title=title)
            
            list = []
            for i, tag in enumerate(tags):
                try:
                    cap_element = tag.find('span', class_='numero__capitulo')
                    if not cap_element:
                        ScraperLogger.warning(self.name, "getChapters", 
                                            f"Número do capítulo não encontrado no item {i+1}")
                        continue
                    
                    cap = cap_element.get_text()
                    ch_id = tag.get('href')
                    list.append(Chapter(id=ch_id, number=cap, name=title))
                    
                    if i < 3:  # Log apenas os primeiros 3
                        ScraperLogger.debug(self.name, "getChapters", 
                                          f"Capítulo {i+1} processado", 
                                          number=cap, ch_id=ch_id)
                except Exception as ch_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        f"Falha ao processar capítulo {i+1}", 
                                        error=str(ch_error))
            
            list.reverse()
            ScraperLogger.success(self.name, "getChapters", "Capítulos carregados", 
                                total=len(list), manga_title=title)
            return list
            
        except Exception as e:
            ScraperLogger.error(self.name, "getChapters", "Falha ao buscar capítulos", 
                              exception=e, manga_id=link)
            raise
    
    def getPages(self, ch: Chapter) -> Pages:
        ScraperLogger.info(self.name, "getPages", "Iniciando busca de páginas", 
                         chapter=ch.number, chapter_id=ch.id)
        
        try:
            # Garantir URL completa
            if not self.url in ch.id:
                ch.id = f'{self.url}{ch.id}'
                ScraperLogger.debug(self.name, "getPages", "URL completa construída", url=ch.id)
            
            response = Http.get(ch.id)
            ScraperLogger.http_request(self.name, "GET", ch.id, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            scripts = soup.find('div', id='imageContainer')
            
            if not scripts:
                ScraperLogger.error(self.name, "getPages", "Image container not found")
                raise ValueError("Image container not found")
            
            scripts = str(scripts.find_all('script'))
            ScraperLogger.debug(self.name, "getPages", "Scripts extracted", 
                              script_length=len(scripts))
            
            match = re.search(r'const\s+urls\s*=\s*(\[.*?\]);', str(scripts), re.DOTALL)
            if not match:
                ScraperLogger.error(self.name, "getPages", "URLs not found in script")
                raise ValueError("Page URLs not found")
            
            urls = ast.literal_eval(match.group(1))
            ScraperLogger.parsing(self.name, "script URLs", len(urls), 1, 
                                context="URLs extracted from JavaScript")
            
            url_list = []
            for i, url in enumerate(urls):
                full_url = f'{self.url}{url}'
                url_list.append(full_url)
                
                if i < 3:  # Log only the first 3 URLs
                    ScraperLogger.debug(self.name, "getPages", 
                                      f"URL {i+1} processed", 
                                      url=full_url[:50] + "...")
            
            ScraperLogger.success(self.name, "getPages", "Pages loaded", 
                                total=len(url_list), chapter=ch.number)
            return Pages(id=ch.id, number=ch.number, name=ch.name, pages=url_list)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getPages", "Failed to fetch pages", 
                              exception=e, chapter=ch.number)
            raise

        
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        title = sanitize_folder_name(pages.name)
        config = get_config()
        img_path = config.save
        path = os.path.join(img_path,
                            str(title), str(sanitize_folder_name(pages.number)))
        os.makedirs(path, exist_ok=True)
        img_format = config.img
        files = []
        page_number = 0
        for i, page in enumerate(pages.pages):
            response = Http.get(page, headers={'referer': f'{self.url}'})

            zip_content = BytesIO(response.content)

            with ZipFile(zip_content) as zip_file:
                for file_name in zip_file.namelist():
                    if not file_name.endswith('.s'):
                        page_number += 1
                        with zip_file.open(file_name) as file:
                            content = file.read()
                            if not os.path.exists(path):
                                os.makedirs(path)
                            try:
                                img = Image.open(BytesIO(content))
                                img.verify()
                                icc = img.info.get('icc_profile')
                                if img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                file = os.path.join(path, f"%03d{img_format}" % page_number)
                                files.append(file)
                                img.save(file, quality=80, dpi=(72, 72), icc_profile=icc)
                            except:
                                if response.status == 200:
                                    file = os.path.join(path, f"%03d{img_format}" % page_number)
                                    files.append(file)
                                    Path(file).write_bytes(content)

            if fn != None:
                fn(math.ceil(i * 100)/len(pages.pages))
            
        if fn != None:
            fn(math.ceil(len(pages.pages) * 100)/len(pages.pages))
        
        return DChapter(pages.number, files)