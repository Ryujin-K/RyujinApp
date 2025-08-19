from urllib.parse import urljoin
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Manga, Pages
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara

class ImperiodabritanniaProvider(WordPressMadara):
    name = 'Imperio da britannia'
    lang = 'pt-Br'
    domain = ['imperiodabritannia.com']

    def __init__(self):
        self.url = 'https://imperiodabritannia.com/'

        self.path = ''
        
        self.query_mangas = 'div.page-item-detail.manga a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        ua = UserAgent()
        user = ua.chrome
        self.user = ua.chrome
        self.headers = {'host': 'imperiodabritannia.com', 'User-Agent': user, 'referer': f'{self.url}', 'Cookie': 'acesso_legitimo=1'}

    def getManga(self, link: str) -> Manga:
        response = Http.get(link, timeout=getattr(self, 'timeout', None))

        if not response or not getattr(response, "text", None):
            raise Exception(f"Falha ao acessar {link} - status: {getattr(response, 'status_code', '??')}")

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        data = soup.select(self.query_title_for_uri)
        if not data:
            print(f"[DEBUG] Nenhum elemento encontrado com selector '{self.query_title_for_uri}'")
            print(f"[DEBUG] HTML retornado (primeiros 300 chars):\n{response.text[:300]}...")
            raise Exception("Não foi possível extrair o título do mangá")

        element = data.pop()
        title = element.get("content", "").strip() or element.text.strip()

        if not title:
            raise Exception("Título vazio ou não encontrado")

        return Manga(id=link, name=title)


    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | self.headers
        else:
            headers = self.headers
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
    
    def _get_chapters_ajax(self, manga_id):
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        response = Http.post(uri, headers={'Cookie': 'visited=true; wpmanga-reading-history=W3siaWQiOjg4MiwiYyI6IjIzMzU5IiwicCI6MSwiaSI6IiIsInQiOjE3MTk5NjEwODN9XQ%3D%3D'})
        data = self._fetch_dom(response, self.query_chapters)
        if data:
            return data
        else:
            raise Exception('No chapters found (new ajax endpoint)!')

        

