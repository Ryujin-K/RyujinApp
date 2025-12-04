import re
from typing import List
from urllib.parse import unquote, quote
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.download.application.use_cases import DownloadUseCase


class KairosToonsProvider(Base):
    name = 'KairosToons'
    lang = 'pt_Br'
    domain = ['kairostoons.net']

    def __init__(self) -> None:
        self.base_url = 'https://kairostoons.net'
        self.domain_name = 'kairostoons.net'

    def _get_headers(self) -> dict:
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"{self.base_url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _extract_slug(self, link: str) -> str:

        link = unquote(link)

        match = re.search(r'/manga/([^/]+)/', link)
        if match:
            return match.group(1)
        

        match = re.search(r'kairostoons\.net/([^/]+)/?$', link)
        if match:
            return match.group(1)
        

        parts = link.rstrip('/').split('/')
        return parts[-1] if parts else ''

    def _extract_chapter_num(self, link: str) -> str:

        match = re.search(r'/capitulo/([^/]+)/?', link)
        if match:
            return match.group(1)
        return ''

    def getManga(self, link: str) -> Manga:
        slug = self._extract_slug(link)
        
        try:

            manga_url = f"{self.base_url}/{quote(slug)}/"
            response = Http.get(manga_url, headers=self._get_headers())
            
            if response.status == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                title_tag = soup.find('h1')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    return Manga(link, title)

            return Manga(link, slug.replace('-', ' ').title())
            
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar manga: {e}")
            return Manga(link, slug.replace('-', ' ').title())

    def getChapters(self, id: str) -> List[Chapter]:
        slug = self._extract_slug(id)
        chapters_list = []
        seen_chapters = set()
        
        try:
            base_manga_url = f"{self.base_url}/{quote(slug)}/"
            
            response = Http.get(base_manga_url, headers=self._get_headers())
            
            if response.status != 200:
                print(f"[{self.name}] Erro ao buscar manga: {response.status}")
                return chapters_list
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('h1')
            manga_title = title_tag.get_text(strip=True) if title_tag else slug.replace('-', ' ').title()
            
            max_page = 1
            pagination = soup.find('nav', attrs={'aria-label': 'Paginação'})
            if pagination:

                last_page_link = pagination.find('a', attrs={'aria-label': 'Última'})
                if last_page_link:
                    href = last_page_link.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        max_page = int(match.group(1))
            
            print(f"[{self.name}] Encontradas {max_page} páginas de capítulos")
            
            for page_num in range(1, max_page + 1):
                if page_num == 1:

                    page_soup = soup
                else:
                    page_url = f"{base_manga_url}?page={page_num}"
                    page_response = Http.get(page_url, headers=self._get_headers())
                    if page_response.status != 200:
                        print(f"[{self.name}] Erro ao buscar página {page_num}: {page_response.status}")
                        continue
                    page_soup = BeautifulSoup(page_response.content, 'html.parser')

                chapter_links = page_soup.find_all('a', href=re.compile(r'/manga/[^/]+/capitulo/[^/]+/?'))
                
                for link in chapter_links:
                    href = link.get('href', '')

                    if href in seen_chapters:
                        continue
                    seen_chapters.add(href)

                    cap_num = self._extract_chapter_num(href)

                    cap_name = f"Capítulo {cap_num}"

                    chapter_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    
                    chapter = Chapter(chapter_url, cap_name, manga_title)
                    chapters_list.append(chapter)
            
            def get_chapter_num(ch):
                num_str = self._extract_chapter_num(ch.id)
                try:
                    return float(num_str)
                except (ValueError, TypeError):
                    return 0
            
            chapters_list.sort(key=get_chapter_num, reverse=True)
            
            print(f"[{self.name}] Encontrados {len(chapters_list)} capítulos no total")
            
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar capítulos: {e}")
        
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        pages_list = []
        
        try:
            response = Http.get(ch.id, headers=self._get_headers())
            
            if response.status == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                canvases = soup.find_all('canvas', attrs={'data-src-url': True})
                
                for canvas in canvases:
                    src = canvas.get('data-src-url', '')
                    if src:

                        full_url = src if src.startswith('http') else f"{self.base_url}{src}"
                        pages_list.append(full_url)
                
                print(f"[{self.name}] Encontradas {len(pages_list)} páginas")
            else:
                print(f"[{self.name}] Erro ao buscar páginas: {response.status}")
                
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar páginas: {e}")
        
        return Pages(ch.id, ch.number, ch.name, pages_list)

    def download(self, pages: Pages, fn=None, headers=None, cookies=None):
        effective_headers = {}
        if isinstance(headers, dict):
            effective_headers.update(headers)
        
        effective_headers.setdefault('Referer', f'{self.base_url}/')
        effective_headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8')
        effective_headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=effective_headers,
            cookies=cookies
        )
