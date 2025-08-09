from core.providers.infra.template.wordpress_madara import WordPressMadara
from core.__seedwork.infra.http import Http
from urllib.parse import urljoin
from core.download.application.use_cases import DownloadUseCase
from core.providers.domain.entities import Pages

class WinterSunScanProvider(WordPressMadara):
    name = 'Winter sun scan'
    lang = 'pt-Br'
    domain = ['wintersunscan.xyz']

    def __init__(self):
        self.url = 'https://wintersunscan.xyz'

        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | {'Referer': 'https://wintersunscan.xyz/lixo'}
        else:
            headers = {'Referer': 'https://wintersunscan.xyz/lixo'}
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
    
    def _get_chapters_ajax(self, manga_id):
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        response = Http.post(uri, headers={'Cookie': 'visited=true; wpmanga-reading-history=W3siaWQiOjg4MiwiYyI6IjIzMzU5IiwicCI6MSwiaSI6IiIsInQiOjE3MTk5NjEwODN9XQ%3D%3D'})
        data = self._fetch_dom(response, self.query_chapters)
        if data:
            return data
        else:
            raise Exception('No chapters found (new ajax endpoint)!')