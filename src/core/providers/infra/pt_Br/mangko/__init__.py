import re
from typing import List
from urllib.parse import unquote
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.download.application.use_cases import DownloadUseCase
from core.config.login_data import insert_login, LoginData, get_login, delete_login
import requests


class MangkoProvider(Base):
    name = 'Mangko'
    lang = 'pt_Br'
    domain = ['mangko.net']

    def __init__(self) -> None:
        self.base_url = 'https://mangko.net'
        self.domain_name = 'mangko.net'
        self._session = None
        self._cookies = {}
        self._session_initialized = False

    def _init_session(self) -> None:

        if self._session_initialized:
            return

        login_info = get_login(self.domain_name)
        if login_info and login_info.cookies:
            self._cookies = login_info.cookies
            self._session_initialized = True
            print(f"[{self.name}] Sessão carregada do cache")
            return
        
        try:
            session = requests.Session()
            session.headers.update(self._get_headers())
            
            r = session.get(self.base_url)
            if r.status_code == 200:
                self._cookies = dict(session.cookies)

                insert_login(LoginData(
                    self.domain_name,
                    {},  # headers
                    self._cookies  # cookies
                ))
                
                self._session_initialized = True
                print(f"[{self.name}] Sessão iniciada com cookies")
        except Exception as e:
            print(f"[{self.name}] Erro ao iniciar sessão: {e}")
        
        self._session = session

    def _get_session(self) -> requests.Session:

        self._init_session()
        
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self._get_headers())
            if self._cookies:
                self._session.cookies.update(self._cookies)
        
        return self._session

    def _get_headers(self) -> dict:
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"{self.base_url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _extract_slug(self, link: str) -> str:

        link = unquote(link)

        match = re.search(r'/comic/([^/]+)', link)
        if match:
            return match.group(1)

        parts = link.rstrip('/').split('/')
        return parts[-1] if parts else ''

    def _extract_chapter_uuid(self, link: str) -> str:

        match = re.search(r'/chapter/([a-f0-9-]+)', link)
        if match:
            return match.group(1)
        return ''

    def getManga(self, link: str) -> Manga:
        slug = self._extract_slug(link)
        
        try:
            manga_url = f"{self.base_url}/comic/{slug}"
            session = self._get_session()
            response = session.get(manga_url)
            
            if response.status_code == 200:
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
            manga_url = f"{self.base_url}/comic/{slug}"
            session = self._get_session()
            response = session.get(manga_url)
            
            if response.status_code != 200:
                print(f"[{self.name}] Erro ao buscar manga: {response.status_code}")
                return chapters_list
            
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.find('h1')
            manga_title = title_tag.get_text(strip=True) if title_tag else slug.replace('-', ' ').title()

            chapter_spans = soup.find_all('span', string=re.compile(r'Chapter\s*\d+'))
            
            for span in chapter_spans:
                chapter_text = span.get_text(strip=True)

                cap_match = re.search(r'Chapter\s*(\d+(?:\.\d+)?)', chapter_text, re.IGNORECASE)
                if cap_match:
                    cap_num = cap_match.group(1)
                    cap_name = f"Capítulo {cap_num}"
                else:
                    cap_name = chapter_text

                parent = span.parent
                link = None
                while parent and not link:
                    link = parent.find('a', href=re.compile(r'/chapter/'))
                    parent = parent.parent
                
                if link:
                    href = link.get('href', '')

                    if href in seen_chapters:
                        continue
                    seen_chapters.add(href)
                    
                    chapter_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    
                    chapter = Chapter(chapter_url, cap_name, manga_title)
                    chapters_list.append(chapter)

            def get_chapter_num(ch):
                match = re.search(r'(\d+(?:\.\d+)?)', ch.name)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        return 0
                return 0
            
            chapters_list.sort(key=get_chapter_num, reverse=True)
            
            print(f"[{self.name}] Encontrados {len(chapters_list)} capítulos")
            
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar capítulos: {e}")
        
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        pages_list = []
        
        try:
            session = self._get_session()
            response = session.get(ch.id)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                images = soup.find_all('img', src=re.compile(r'/proxy/image/'))
                
                for img in images:
                    src = img.get('src', '')
                    if src:
                        full_url = src if src.startswith('http') else f"{self.base_url}{src}"
                        pages_list.append(full_url)

                if not pages_list:
                    images = soup.find_all('img', attrs={'data-src': re.compile(r'/proxy/image/')})
                    for img in images:
                        src = img.get('data-src', '')
                        if src:
                            full_url = src if src.startswith('http') else f"{self.base_url}{src}"
                            pages_list.append(full_url)
                
                print(f"[{self.name}] Encontradas {len(pages_list)} páginas")
            else:
                print(f"[{self.name}] Erro ao buscar páginas: {response.status_code}")
                
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar páginas: {e}")
        
        return Pages(ch.id, ch.number, ch.name, pages_list)

    def download(self, pages: Pages, fn=None, headers=None, cookies=None):

        self._init_session()
        
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
