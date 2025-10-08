from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Pages, Chapter, Manga
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara

class HuntersScanProvider(WordPressMadara):
    name = 'Hunters scan'
    lang = 'pt-Br'
    domain = ['hunterscomics.com', 'readhunters.xyz']

    def __init__(self):
        self.url = 'https://readhunters.xyz'
        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_pages_img = 'div.reading-content img.wp-manga-chapter-img'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        
        ua = UserAgent()
        user = ua.chrome
        self.headers = {
            'User-Agent': user,
            'Referer': f'{self.url}/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Cookie': 'acesso_legitimo=1',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.url,
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.timeout = 10

    def getChapters(self, id: str):
        try:
            uri = urljoin(self.url, id)
            response = Http.get(uri, timeout=self.timeout, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = soup.select(self.query_title_for_uri)
            title = data.pop()['content'].strip() if data else 'Unknown'
            
            placeholder = soup.select_one(self.query_placeholder)
            
            if placeholder:
                return self._get_all_chapters_paginated(id, title)
            else:
                chapters = []
                for el in soup.select(self.query_chapters):
                    ch_id = self.get_root_relative_or_absolute_link(el, uri)
                    chapters.append(Chapter(ch_id, el.text.strip(), title))
                chapters.reverse()
                return chapters
            
        except Exception:
            return []
    
    def _get_all_chapters_paginated(self, manga_id, title):
        if not manga_id.endswith('/'):
            manga_id += '/'
        
        ajax_url = urljoin(self.url, f'{manga_id}ajax/chapters/')
        all_chapters = []
        
        response = Http.post(ajax_url, timeout=self.timeout, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pagination_links = soup.select('a[data-page]')
        max_page = max([int(link.get('data-page', 1)) for link in pagination_links]) if pagination_links else 1
        
        for page in range(1, max_page + 1):
            try:
                if page > 1:
                    response = Http.post(ajax_url, params={'t': page}, timeout=self.timeout, headers=self.headers)
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                for el in soup.select(self.query_chapters):
                    ch_id = self.get_root_relative_or_absolute_link(el, ajax_url)
                    if ch_id:
                        all_chapters.append(Chapter(ch_id, el.text.strip(), title))
                
            except Exception:
                continue
        
        seen = set()
        unique_chapters = [ch for ch in all_chapters if ch.id not in seen and not seen.add(ch.id)]
        unique_chapters.reverse()
        return unique_chapters
    
    def getPages(self, ch: Chapter) -> Pages:
        urls = self._get_images_http(ch.id)
        num = re.findall(r'\d+\.?\d*', str(ch.number))
        number = num[0] if num else ch.number
        return Pages(ch.id, number, ch.name, urls)

    def _get_images_http(self, url_capitulo: str):
        try:
            r = Http.get(url_capitulo, headers=self.headers, timeout=self.timeout)
            if r.status not in range(200, 299):
                return []
            soup = BeautifulSoup(r.content, 'html.parser')
            selectors = [self.query_pages_img, 'div.page-break img', 'div.reading-content img']
            imgs = []
            for sel in selectors:
                imgs = soup.select(sel)
                if imgs: break
            if not imgs: return []
            urls = []
            for img in imgs:
                for attr in ('src','data-src','data-lazy-src','data-original'):
                    v = (img.get(attr) or '').strip()
                    if v:
                        if v.startswith('//'): v = 'https:' + v
                        if v.startswith('/'): v = urljoin(self.url, v)
                        if '/WP-manga/data/' in v and v.lower().endswith(('.jpg','.jpeg','.png','.webp')):
                            urls.append(v); break
            seen = set(); urls = [u for u in urls if not (u in seen or seen.add(u))]
            def num(u):
                f = u.split('/')[-1].split('?')[0]
                m = re.search(r'(\d+)', f); return int(m.group(1)) if m else 0
            return sorted(urls, key=num)
        except Exception:
            return []
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        image_headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': pages.id,
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'acesso_legitimo=1',
            'Origin': self.url,
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        if headers:
            image_headers.update(headers)
        
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=image_headers, cookies=cookies, timeout=self.timeout)