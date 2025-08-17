import time
from urllib.parse import urljoin
import undetected_chromedriver as uc
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
        desktop_ua = ua.chrome
        self.user = ua.chrome

        self.headers = {
            'Host': 'imperiodabritannia.com',
            'User-Agent': desktop_ua,
            'Referer': f'{self.url}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': 'acesso_legitimo=1',
            'Connection': 'keep-alive',
        }

        print("[Imperio] Provider inicializado com headers:", self.headers)

    def fetch_with_undetected_chrome(self, url: str, headless=True) -> str:
        """Abre a página com Chrome não detectado e retorna o HTML completo."""
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument(f"user-agent={self.headers.get('User-Agent')}")
        
        driver = uc.Chrome(options=options, headless=headless)
        try:
            driver.get(url)
            # Espera mínima para o conteúdo carregar
            time.sleep(3)

            # Se houver Turnstile, manual ou automático via loop
            attempts = 0
            while "verificando" in driver.page_source.lower() and attempts < 5:
                print("[Cloudflare] Aguardando Turnstile ser liberado...")
                time.sleep(2)
                attempts += 1

            html = driver.page_source
            return html
        finally:
            driver.quit()

    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | self.headers
        else:
            headers = self.headers

        print(f"[Imperio] Iniciando download de {len(pages)} páginas")
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)
    
    def _get_chapters_ajax(self, manga_id):
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        print(f"[Imperio] Requisitando capítulos via AJAX em {uri}")

        try:
            response = Http.post(
                uri,
                headers={
                    'Cookie': 'visited=true; wpmanga-reading-history=W3siaWQiOjg4MiwiYyI6IjIzMzU5IiwicCI6MSwiaSI6IiIsInQiOjE3MTk5NjEwODN9XQ%3D%3D'
                }
            )
        except Exception as e:
            print(f"[Imperio] ERRO na request POST: {e}")
            raise

        print(f"[Imperio] Status da resposta: {getattr(response, 'status_code', 'sem status')}")
        print(f"[Imperio] Tamanho do conteúdo recebido: {len(response.content) if hasattr(response, 'content') else 'sem content'}")

        data = self._fetch_dom(response, self.query_chapters)
        if data:
            print(f"[Imperio] {len(data)} capítulos encontrados no AJAX")
            return data
        else:
            print("[Imperio] Nenhum capítulo encontrado no AJAX!")
            raise Exception('No chapters found (new ajax endpoint)!')
