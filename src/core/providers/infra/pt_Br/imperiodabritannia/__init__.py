from urllib.parse import urljoin
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Pages
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara

class ImperiodabritanniaProvider(WordPressMadara):
    name = 'Imperio da britannia'
    lang = 'pt-Br'
    domain = ['imperiodabritannia.com']

    def __init__(self):
        self.url = 'https://imperiodabritannia.com/'
        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        
        ua = UserAgent()
        user_agent = ua.chrome
        self.user = user_agent
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en,pt;q=0.9,es-US;q=0.8,es-419;q=0.7,es;q=0.6',
            'Cache-Control': 'no-cache',
            'Origin': 'https://imperiodabritannia.com',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': user_agent,
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | self.headers
        else:
            headers = self.headers
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
    
    def _get_chapters_ajax(self, manga_id, referer=None):
        if not manga_id.endswith('/'):
            manga_id += '/'
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        headers = self._prepare_headers(
            referer=referer or urljoin(self.url, manga_id),
            extra={'X-Requested-With': 'XMLHttpRequest'}
        )
        response = Http.post(
            uri,
            headers=headers,
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )
        data = self._fetch_dom(response, self.query_chapters)
        if data:
            return data
        else:
            raise Exception('No chapters found (new ajax endpoint)!')