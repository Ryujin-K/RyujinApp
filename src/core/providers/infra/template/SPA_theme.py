import json
from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from urllib.parse import urljoin, urlencode, urlparse, quote
import re

class SPATheme(Base):
    """
    Template base para sites que usam SPATheme
    Baseado no zerotheme do keiyoushi/extensions-source
    Adaptado para o padrão do RyujinApp
    """
    
    def __init__(self):
        self.base_url = ''
        self.source_path = ''  # Caminho base para imagens/recursos
        self.manga_sub_string = 'comics'  # Substring para URLs de mangás
        self.chapter_sub_string = 'chapters'  # Substring para URLs de capítulos
        self.timeout = None
        
        # Headers padrão para requisições
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }

    def _get_json_from_props(self, html: str) -> dict:
        """Extrai dados JSON do __NEXT_DATA__ ou props similar"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Busca por script com __NEXT_DATA__
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data and next_data.string:
                return json.loads(next_data.string)
            
            # Busca por scripts com dados JSON
            for script in soup.find_all('script', type='application/json'):
                if script.string:
                    try:
                        return json.loads(script.string)
                    except json.JSONDecodeError:
                        continue
            
            # Busca padrões de props no HTML
            props_match = re.search(r'props"\s*:\s*({.*?})', html, re.DOTALL)
            if props_match:
                return json.loads(props_match.group(1))
                
        except Exception:
            pass
        
        return {}

    def _parse_manga_from_json(self, manga_data: dict) -> Manga:
        """Converte dados JSON do manga para objeto Manga"""
        try:
            title = manga_data.get('title', 'Título não encontrado')
            slug = manga_data.get('slug', '')
            description = manga_data.get('description', '')
            
            # Remove HTML da descrição se presente
            if description:
                description = BeautifulSoup(description, 'html.parser').get_text(strip=True)
            
            return Manga(id=slug, name=title, description=description)
        except Exception:
            return Manga(id='', name='Erro ao carregar manga')

    def _parse_chapters_from_json(self, chapters_data: List[dict], manga_name: str) -> List[Chapter]:
        """Converte lista de capítulos JSON para objetos Chapter"""
        try:
            chapters = [Chapter(
                id=ch.get('chapter_path', '').split('/')[-1] if ch.get('chapter_path') else str(ch.get('chapter_number', 0)),
                name=manga_name,
                number=str(ch.get('chapter_number', 0))
            ) for ch in chapters_data]
            
            # Ordena capítulos por número
            chapters.sort(key=lambda c: float(c.number) if c.number.replace('.', '').isdigit() else 0)
            return chapters
        except Exception:
            return []

    def _parse_pages_from_json(self, pages_data: dict) -> List[str]:
        """Extrai URLs das páginas do JSON"""
        try:
            page_list = pages_data.get('chapter', {}).get('pages', [])
            pages = []
            
            for page in page_list:
                page_path = page.get('page_path', '')
                if page_path and not page_path.endswith('.xml'):
                    # Constrói URL completa da imagem
                    if page_path.startswith('http'):
                        pages.append(page_path)
                    else:
                        pages.append(f"{self.source_path}/{page_path.lstrip('/')}")
            
            return pages
        except Exception:
            return []

    def getManga(self, link: str) -> Manga:
        """Obtém informações do manga"""
        try:
            url = f"{self.base_url}/{self.manga_sub_string}/{link}" if not link.startswith('http') else link
            response = Http.get(url, headers=self.headers, timeout=getattr(self, 'timeout', None))
            
            # Tenta extrair dados JSON primeiro
            json_data = self._get_json_from_props(response.content.decode('utf-8'))
            
            if json_data:
                # Busca dados do manga nos props
                props = json_data.get('props', {})
                manga_data = props.get('pageProps', {}).get('comic_infos', props.get('content', json_data))
                
                if manga_data:
                    return self._parse_manga_from_json(manga_data)
            
            # Fallback: parse HTML tradicional
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Busca título com seletores priorizados
            title = 'Manga não encontrado'
            for selector in ['h1.text-3xl', 'h1.title', 'h1', 'meta[property="og:title"]', 'title']:
                element = soup.select_one(selector)
                if element:
                    title = element.get('content') if element.name == 'meta' else element.get_text(strip=True)
                    break
            
            slug = link.split('/')[-1] if '/' in link else link
            return Manga(id=slug, name=title)
            
        except Exception:
            slug = link.split('/')[-1] if '/' in link else link
            return Manga(id=slug, name='Erro ao carregar manga')

    def getChapters(self, id: str) -> List[Chapter]:
        """Obtém lista de capítulos"""
        try:
            url = f"{self.base_url}/{self.manga_sub_string}/{id}"
            response = Http.get(url, headers=self.headers, timeout=getattr(self, 'timeout', None))
            
            # Tenta extrair dados JSON
            json_data = self._get_json_from_props(response.content.decode('utf-8'))
            
            if json_data:
                props = json_data.get('props', {})
                manga_data = props.get('pageProps', {}).get('comic_infos', props.get('content', json_data))
                chapters_data = manga_data.get('chapters', [])
                
                if chapters_data:
                    manga_name = manga_data.get('title', 'Manga')
                    return self._parse_chapters_from_json(chapters_data, manga_name)
            
            # Fallback: parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            chapters = []
            manga_name = id.replace('-', ' ').title()
            
            # Busca lista de capítulos com seletores priorizados
            for selector in ['.chapter-list a', '.chapters-list a', '.wp-manga-chapter a', 'a[href*="chapter"]']:
                chapter_links = soup.select(selector)
                if chapter_links:
                    for i, link in enumerate(chapter_links):
                        href = link.get('href', '')
                        if 'chapter' in href.lower():
                            chapter_id = href.split('/')[-1]
                            chapter_text = link.get_text(strip=True)
                            
                            # Extrai número do capítulo
                            number_match = re.search(r'(\d+(?:\.\d+)?)', chapter_text)
                            chapter_number = number_match.group(1) if number_match else str(i + 1)
                            
                            chapters.append(Chapter(id=chapter_id, name=manga_name, number=chapter_number))
                    break
            
            # Ordena capítulos
            chapters.sort(key=lambda c: float(c.number) if c.number.replace('.', '').isdigit() else 0)
            return chapters
            
        except Exception:
            return []

    def getPages(self, chapter: Chapter) -> Pages:
        """Obtém páginas do capítulo"""
        try:
            url = f"{self.base_url}/{self.chapter_sub_string}/{chapter.id}"
            response = Http.get(url, headers=self.headers, timeout=getattr(self, 'timeout', None))
            
            # Tenta extrair dados JSON
            json_data = self._get_json_from_props(response.content.decode('utf-8'))
            pages_urls = []
            
            if json_data:
                props = json_data.get('props', {})
                pages_data = props.get('pageProps', props.get('content', json_data))
                pages_urls = self._parse_pages_from_json(pages_data)
            
            # Fallback: parse HTML
            if not pages_urls:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca imagens com seletores priorizados
                for selector in ['.page-break img', '.chapter-images img', 'img[src*=".jpg"]', 'img[src*=".png"]', 'img[src*=".webp"]']:
                    images = soup.select(selector)
                    if images:
                        for img in images:
                            src = img.get('src') or img.get('data-src')
                            if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                # Normaliza URL
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    src = self.base_url + src
                                elif not src.startswith('http'):
                                    src = urljoin(self.base_url, src)
                                pages_urls.append(src)
                        break
            
            return Pages(id=chapter.id, number=chapter.number, name=chapter.name, pages=pages_urls)
            
        except Exception:
            return Pages(id=chapter.id, number=chapter.number, name=chapter.name, pages=[])