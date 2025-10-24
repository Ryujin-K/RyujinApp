from core.providers.infra.template.wordpress_madara import WordPressMadara
from core.providers.domain.entities import Chapter, Pages, Manga
from bs4 import BeautifulSoup
import re
import json
import base64
from core.__seedwork.infra.http import Http
from urllib.parse import urljoin, urlparse, parse_qs

class CeriseScanProvider(WordPressMadara):
    name = 'Cerise Scan'
    lang = 'pt-Br'
    domain = ['loverstoon.com']

    def __init__(self):
        self.url = 'https://loverstoon.com'
        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'img'
        self.query_title_for_uri = 'h1'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'

    def getPages(self, ch: Chapter) -> Pages:
        uri = urljoin(self.url, ch.id)
        response = Http.get(uri, timeout=getattr(self, 'timeout', None))
        soup_real = BeautifulSoup(response.content, 'html.parser')
        
        guardian_link = soup_real.select_one("div.page-break > a")
        href = guardian_link.get('href')
        
        image_urls = self._decode_guardian_auth(href)
        
        number = re.findall(r'\d+\.?\d*', str(ch.number))[0]
        return Pages(ch.id, number, ch.name, image_urls)
    
    def _decode_guardian_auth(self, guardian_url: str) -> list:

        try:
            parsed = urlparse(guardian_url)
            params = parse_qs(parsed.query)
            
            if 'auth' not in params:
                return []
            
            auth_encoded = params['auth'][0]
            
            auth_decoded = base64.b64decode(auth_encoded).decode('utf-8')
            
            auth_data = json.loads(auth_decoded)
            
            if 'url' in auth_data:
                urls_string = auth_data['url']
                image_urls = [url.strip() for url in urls_string.split(';') if url.strip()]
                return image_urls
            
            return []
        
        except Exception as e:
            print(f"Erro ao decodificar guardian auth: {e}")
            return []
        