import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.manga_reader_cms import MangaReaderCms
from core.config.login_data import get_login, delete_login, insert_login, LoginData

class YomuComicsProvider(MangaReaderCms):
    name = 'Yomu Comics'
    lang = 'pt-Br'
    domain = ['yomucomics.com','yomu.com.br']
    has_login = True

    def __init__(self):
        super().__init__()
        self.url = 'https://yomu.com.br'
        self.path = '/'
        self.login_url = f'{self.url}/auth/login'
        self.domain = 'yomu.com.br'
        self._api_series = f'{self.url}/api/public/series/'
        self._api_chapters = f'{self.url}/api/public/chapters/'
        self._web_series = f'{self.url}/obra/'

    def _is_login_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.lower() if soup.title and soup.title.string else ''
        return 'login' in title

    def login(self):
        login_info = get_login(self.domain)
        if login_info:
            test = Http.get(self.url)
            if self._is_login_page(test.text() if test else ''):
                delete_login(self.domain)
                login_info = None
        return bool(login_info)

    def getManga(self, link: str) -> Manga:
        api_link = link.replace(self._web_series, self._api_series)
        r = Http.get(api_link)
        data = r.json() if r and r.status == 200 else {}
        title = data.get('name') or 'Desconhecido'
        return Manga(link, title)

    def getChapters(self, id: str):
        api_link = id.replace(self._web_series, self._api_series)
        r = Http.get(api_link)
        data = r.json() if r and r.status == 200 else {}
        chs = data.get('chapters', [])
        series_id = data.get('id')
        title = f"{data.get('name')} - {series_id}" if series_id else data.get('name')
        base = id.replace('obra', 'ler').rstrip('/')
        out = []
        for c in chs:
            idx = c.get('index')
            if idx is None: continue
            out.append(Chapter(f"{base}/{idx}", str(idx), title))
        out.reverse()
        return out

    def getPages(self, ch: Chapter) -> Pages:
        try:
            title_part, sid = ch.name.split(' - ')
            ch.name = title_part
        except ValueError:
            sid = ''
        images_api = f"{self._api_chapters}{sid}/{ch.number}"
        r = Http.get(images_api)
        data = r.json() if r and r.status == 200 else {}
        pages = []
        for p in data.get('pages', []):
            u = p.get('url')
            if u:
                pages.append(urljoin(self.url, u))
        return Pages(ch.id, ch.number, ch.name, pages)