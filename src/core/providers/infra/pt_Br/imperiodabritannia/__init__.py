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
    
    def _get_chapters_ajax(self, manga_id):
        return self._get_chapters_ajax_britannia(manga_id)
    
    def _get_chapters_ajax_britannia(self, manga_id):
        if manga_id.startswith('http'):
            manga_slug = manga_id.split('/manga/')[-1].rstrip('/')
        else:
            manga_slug = manga_id.rstrip('/')
        
        print(f"[DEBUG] ImperiodabritanniaProvider._get_chapters_ajax called with manga_id: {manga_id}")
        uri = urljoin(self.url, f'manga/{manga_slug}/ajax/chapters/?t=1')
        print(f"[DEBUG] URI gerada: {uri}")
        ajax_headers = self.headers.copy()
        ajax_headers['Referer'] = f'https://imperiodabritannia.com/manga/{manga_slug}/'
        
        response = Http.post(uri, data='', headers=ajax_headers)
        if response.status == 200:
            from core.__seedwork.infra.http.contract.http import Response
            fixed_response = Response(response.status, response.data, response.data, response.url)
            data = self._fetch_dom(fixed_response, self.query_chapters)
            if data:
                return data
                
        raise Exception('No chapters found (ajax endpoint failed)!')