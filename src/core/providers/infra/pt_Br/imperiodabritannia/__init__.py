import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from core.providers.domain.entities import Chapter, Pages, Manga
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara


class ImperiodabritanniaProvider(WordPressMadara):
    name = 'Imperio da britannia'
    lang = 'pt-Br'
    domain = ['imperiodabritannia.com']

    def __init__(self):
        super().__init__()
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
        self.headers = {
            'User-Agent': desktop_ua,
            'Referer': self.url
        }
        self.cookies = None  # <--- armazenar cookies aqui
        print("[Imperio] Provider inicializado com Selenium + Undetected Chrome")

    # ------------------ Cookies Helpers ------------------
    def _save_cookies(self, driver, path="cookies.json"):
        with open(path, "w") as f:
            json.dump(driver.get_cookies(), f)

    def _load_cookies(self, path="cookies.json"):
        try:
            with open(path, "r") as f:
                cookies = json.load(f)
                return {c["name"]: c["value"] for c in cookies}
        except FileNotFoundError:
            return None

    # ------------------ Selenium fetch ------------------
    def _get_html(self, url: str, headless=False) -> str:

        # Selenium
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={self.headers['User-Agent']}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")

        driver = uc.Chrome(options=options, headless=headless)
        try:
            driver.get(url)
            time.sleep(10)
            attempts = 0
            while "verificando" in driver.page_source.lower() and attempts < 5:
                print("[Cloudflare] Aguardando Turnstile ser liberado...")
                time.sleep(5)
                attempts += 1

            # salva cookies
            self._save_cookies(driver)
            self.cookies = {c["name"]: c["value"] for c in driver.get_cookies()}

            return driver.page_source
        finally:
            driver.quit()

    # ------------------ Override WordPressMadara methods ------------------
    def getManga(self, link: str) -> Manga:
        html = self._get_html(link)
        soup = BeautifulSoup(html, 'html.parser')
        
        h1 = soup.select_one("div#manga-title h1")
        if h1:
            title = ''.join([t for t in h1.contents if isinstance(t, str)]).strip()
        else:
            element = soup.select_one(self.query_title_for_uri)
            title = element['content'].strip() if element and 'content' in element.attrs else element.text.strip()
        
        return Manga(id=link, name=title)

    def getChapters(self, id: str):
        if not id.endswith('/'):
            id += '/'
        url = urljoin(self.url, id)
        html = self._get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        elements = soup.select("ul.main.version-chap.no-volumn.active li.wp-manga-chapter a")
        chs = []
        ch_name = soup.select_one(self.query_title_for_uri).text.strip()

        for el in elements:
            ch_id = self.get_root_relative_or_absolute_link(el, url)
            ch_number = el.text.strip()
            chs.append(Chapter(ch_id, ch_number, ch_name))

        chs.reverse()
        return chs

    def getPages(self, ch: Chapter) -> Pages:
        url = urljoin(self.url, ch.id)
        url = self._add_query_params(url, {'style': 'list'})
        html = self._get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.select(self.query_pages)
        if not data:
            url = self._remove_query_params(url, ['style'])
            html = self._get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            data = soup.select(self.query_pages)

        pages_list = []
        for el in data:
            pages_list.append(self._process_page_element(el, url))

        number = re.findall(r'\d+\.?\d*', str(ch.number))[0]
        return Pages(ch.id, number, ch.name, pages_list)

    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        print(f"[Imperio] Iniciando download de {len(pages)} páginas")
        # usa cookies salvos
        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=headers or self.headers,
            cookies=cookies or self.cookies
        )
