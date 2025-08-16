from urllib.parse import urljoin, urlencode
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
        
        self.query_mangas = '#loop-content .item-thumb a'
        self.query_chapters = 'ul.main.version-chap li.wp-manga-chapter a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break img.wp-manga-chapter-img'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        ua = UserAgent()
        self.user = ua.chrome
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Referer": "https://imperiodabritannia.com/",
            "Origin": "https://imperiodabritannia.com",
            "Connection": "keep-alive",
        }
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | self.headers
        else:
            headers = self.headers
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
    
    def _get_chapters_ajax(self, manga_id):
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        print(f"[DEBUG] Fazendo request para: {uri}")
        
        # headers mais realistas
        headers = self.headers | {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.url}manga/{manga_id}/"
        }

        # tenta com requests
        response = Http.post(uri, headers=headers, cookies={'visited': 'true'})
        print(f"[DEBUG] Response retornado: {response}")

        if response is None:
            raise Exception(f"[ERRO] Falha ao acessar {uri}, Http.post retornou None")
        
        try:
            data = self._fetch_dom(response, self.query_chapters)
            print(f"[DEBUG] Chapters encontrados: {data}")
        except Exception as e:
            print(f"[ERRO] _fetch_dom quebrou: {e}")
            raise
        
        if data:
            return data
        else:
            raise Exception('[ERRO] Nenhum capítulo encontrado (ajax endpoint)')
        
    def _create_manga_request(self, page):
        form = {
            'action': 'madara_load_more',
            'template': 'madara-core/content/content-archive',
            'page': page,
            'vars[paged]': '0',
            'vars[post_type]': 'wp-manga',
            'vars[posts_per_page]': '250'
        }
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'x-referer': self.url
        }
        request_url = urljoin(self.url, f'{self.path}/wp-admin/admin-ajax.php')

        response = Http.post(
            request_url,
            data=urlencode(form),
            headers=headers,
            timeout=getattr(self, 'timeout', None)
        )

        # 🔒 Validação para evitar NoneType
        if response is None:
            raise RuntimeError(
                f"❌ Falha ao obter resposta em {request_url} (página {page})."
            )

        if not hasattr(response, "content") or response.content is None:
            raise RuntimeError(
                f"❌ Resposta inválida em {request_url} (página {page}), sem conteúdo."
            )

        return response
