from typing import List, Tuple
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.__seedwork.infra.http import Http
from bs4 import BeautifulSoup
import re
import json
import html

class ReadMangasProvider(Base):
    name = 'Read Mangas'
    lang = 'pt_Br'
    domain = ['www.readmangas.org']

    def __init__(self) -> None:
        super().__init__()
        self.base_url = 'https://www.readmangas.org'
        self.source_path = 'https://www.readmangas.org'
        self.manga_sub_string = 'comic'
        self.chapter_sub_string = 'chapter'
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _get_json_from_props(self, html: str) -> dict:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # ReadMangas usa Inertia.js, não Next.js
            app_div = soup.find('div', id='app')
            if not app_div or not app_div.get('data-page'):
                return {}
            
            json_data = app_div.get('data-page')
            
            patterns = {
                'title': r'"title":"([^"]*)"',
                'slug': r'"slug":"([^"]*)"',
                'chapters': r'"comic_infos":\{.*?"chapters":\[(.*?)\].*?"genres":'
            }
            
            matches = {key: re.search(pattern, json_data) for key, pattern in patterns.items()}
            
            if all(matches.values()):
                return {
                    "props": {
                        "pageProps": {
                            "comic_infos": {
                                "title": matches['title'].group(1),
                                "slug": matches['slug'].group(1),
                                "chapters": json.loads(f"[{matches['chapters'].group(1)}]")
                            }
                        }
                    }
                }
            
            return {}
            
        except Exception as e:
            print(f"Erro ao extrair dados Inertia: {e}")
            return {}

    def _parse_manga_from_json(self, manga_data: dict) -> Manga:
        try:
            title = html.unescape(manga_data.get('title', 'Título não encontrado'))
            slug = manga_data.get('slug', '')
            return Manga(id=slug, name=title)
        except Exception as e:
            print(f"Erro ao parsear manga: {e}")
            return Manga(id='', name='Erro ao carregar manga')

    def _parse_chapters_from_json(self, chapters_data: List[dict], manga_name: str) -> List[Chapter]:
        chapters = []
        try:
            manga_name = html.unescape(manga_name)
            
            for chapter_data in chapters_data:
                chapter_number = str(chapter_data.get('chapter_number', ''))
                chapter_path = chapter_data.get('chapter_path', '')  # UUID do ReadMangas
                
                chapters.append(Chapter(
                    id=chapter_path if chapter_path else str(chapter_data.get('id', '')),
                    name=manga_name,
                    number=chapter_number
                ))
            
            def sort_key(c: Chapter) -> Tuple[int, float]:
                try:
                    return (0, float(c.number))
                except ValueError:
                    return (1, float('inf'))
            
            chapters.sort(key=sort_key)
            return chapters
        except Exception as e:
            print(f"Erro ao parsear capítulos: {e}")
            return []

    def _parse_pages_from_json(self, pages_data: dict) -> List[str]:
        try:
            return []
        except Exception as e:
            print(f"Erro ao parsear páginas: {e}")
            return []

    def getPages(self, chapter: Chapter) -> Pages:
        try:
            chapter_url = f"{self.base_url}/{self.chapter_sub_string}/{chapter.id}"
            response = Http.get(chapter_url, headers=self.headers, timeout=10)
            
            soup = BeautifulSoup(response.text(), 'html.parser')
            app_div = soup.find('div', id='app')
            if app_div and app_div.get('data-page'):
                json_data = app_div.get('data-page')
                
                pages_match = re.search(r'"pages":\[(.*?)\]', json_data)
                url_cdn_match = re.search(r'"url_cdn":"([^"]*)"', json_data)
                
                if pages_match and url_cdn_match:
                    url_cdn = url_cdn_match.group(1).replace('\\/', '/')
                    page_paths = re.findall(r'"page_path":"([^"]*)"', pages_match.group(1))
                    
                    if page_paths:
                        image_urls = []
                        for page_path in page_paths:
                            page_path = page_path.replace('\\/', '/').replace('\\', '')
                            image_url = f"{url_cdn}/{page_path}".replace('\\/', '/').replace('\\', '')
                            image_urls.append(image_url)
                        
                        return Pages(
                            id=chapter.id,
                            number=chapter.number,
                            name=chapter.name,
                            pages=image_urls
                        )
            
            return super().getPages(chapter)
            
        except Exception as e:
            print(f"Erro em getPages: {e}")
            return Pages(id=chapter.id, number=chapter.number, name=chapter.name, pages=[])