import os
import re
import json
import time
import asyncio
import cv2  # type: ignore
import nodriver as uc
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Chapter, Manga, Pages
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara
from core.config.login_data import get_login, insert_login, delete_login, LoginData
from core.cloudflare.infra.nodriver.chrome import find_chrome_executable


class ManhastroProvider(WordPressMadara):
    name = 'Manhastro'
    lang = 'pt-Br'
    domain = ['manhastro.net']
    has_login = True

    api_base = 'https://api2.manhastro.net'
    dataset_cache: Dict[str, dict] = {}
    dataset_cache_ts: float = 0.0
    dataset_cache_ttl: int = 60 * 30  # 30 minutes

    def __init__(self):
        self.url = 'https://manhastro.net/'
        self.path = ''
        self.headers = None
        self.cookies = None

        self.login_pages = (
            urljoin(self.url, 'login'),
            urljoin(self.url, 'minha-conta/'),
        )
        self.login_url = self.login_pages[0]
        self._login_domains = ('manhastro.net',)
        self._login_domain = self._login_domains[0]

        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'

    def _extract_login_html(self, content: bytes | str | None) -> str:
        if isinstance(content, (bytes, bytearray)):
            return content.decode('utf-8', errors='ignore')
        return content or ''

    def _is_login_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, 'html.parser')
        selectors = (
            'form#loginform',
            'form.woocommerce-form-login',
            'form[id*="login"]',
            'form[name*="login"]',
            'form[action*="login"]',
            'form[action*="minha-conta"]',
        )
        forms = [soup.select_one(selector) for selector in selectors]
        forms = [form for form in forms if form]
        for form in forms:
            if form.find('input', {'type': 'password'}):
                return True
        # Fallback: search for explicit login button without catching the homepage hero text
        inputs = soup.select('form input[type="password"]')
        return bool(inputs)

    def _filter_cookies(self, cookies) -> Tuple[dict, Optional[str]]:
        filtered = {}
        detected_domain = None
        allowed = [d.lstrip('.') for d in self._login_domains]
        for cookie in cookies or []:
            domain = (getattr(cookie, 'domain', '') or '').lstrip('.')
            if any(domain.endswith(item) for item in allowed):
                filtered[cookie.name] = cookie.value
                if detected_domain is None:
                    detected_domain = next((d for d in self._login_domains if domain.endswith(d)), None)
        return filtered, detected_domain

    def _has_auth_cookie(self, cookies: dict) -> bool:
        prefixes = (
            'wordpress_logged_in',
            'wp_woocommerce_session',
            'manhastro',
            'session',
        )
        return any(name.startswith(prefix) for name in cookies for prefix in prefixes)

    def _apply_login_context(self, headers: dict | None, cookies: dict | None) -> None:
        self.headers = headers.copy() if isinstance(headers, dict) else None
        self.cookies = cookies.copy() if isinstance(cookies, dict) else None

    def _ensure_valid_login(self) -> bool:
        for domain in self._login_domains:
            login_info = get_login(domain)
            if not login_info:
                continue
            try:
                response = Http.get(self.url, headers=login_info.headers, cookies=login_info.cookies)
                html = self._extract_login_html(response.content)
                if self._is_login_page(html):
                    delete_login(domain)
                    continue
                self._login_domain = domain
                self._apply_login_context(login_info.headers, login_info.cookies)
                return True
            except Exception:
                delete_login(domain)
        return False

    def login(self):
        if self._ensure_valid_login():
            return

        async def perform_login():
            start_kwargs = {}
            chrome_path = find_chrome_executable()
            if chrome_path:
                start_kwargs['browser_executable_path'] = chrome_path
            browser = await uc.start(**start_kwargs)
            try:
                page = None
                for candidate in self.login_pages:
                    try:
                        page = await browser.get(candidate)
                        break
                    except Exception:
                        continue
                if page is None:
                    page = await browser.get(self.url)

                attempts = 0
                max_attempts = 240
                while attempts < max_attempts:
                    attempts += 1
                    cookies = await browser.cookies.get_all()
                    cookie_map, detected_domain = self._filter_cookies(cookies)
                    if self._has_auth_cookie(cookie_map):
                        if detected_domain:
                            self._login_domain = detected_domain
                        agent = await page.evaluate('navigator.userAgent')
                        headers = {'User-Agent': agent}
                        insert_login(LoginData(self._login_domain, headers, cookie_map))
                        self._apply_login_context(headers, cookie_map)
                        return

                    html_page = await page.get_content()
                    if not self._is_login_page(html_page):
                        cookies = await browser.cookies.get_all()
                        cookie_map, detected_domain = self._filter_cookies(cookies)
                        if cookie_map:
                            if detected_domain:
                                self._login_domain = detected_domain
                            agent = await page.evaluate('navigator.userAgent')
                            headers = {'User-Agent': agent}
                            insert_login(LoginData(self._login_domain, headers, cookie_map))
                            self._apply_login_context(headers, cookie_map)
                            return
                    await asyncio.sleep(1)

                raise RuntimeError('Tempo esgotado aguardando o login no Manhastro.')
            finally:
                browser.stop()

        uc.loop().run_until_complete(perform_login())

    def _request_json(self, endpoint: str) -> dict:
        endpoint = endpoint.lstrip('/')
        api_url = urljoin(self.api_base + '/', endpoint)
        response = Http.get(
            api_url,
            headers=self._prepare_headers(referer=self.url, extra={'Accept': 'application/json'}),
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )
        raw = response.data if isinstance(response.data, str) else response.text()
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8', errors='ignore')
        raw = raw or ''
        if raw.startswith('_'):
            raw = raw[1:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Falha ao converter JSON de {api_url}: {exc}') from exc

    @classmethod
    def _get_dataset(cls, fetcher: Callable[[str], dict]) -> Dict[str, dict]:
        now = time.time()
        if cls.dataset_cache and (now - cls.dataset_cache_ts) < cls.dataset_cache_ttl:
            return cls.dataset_cache

        data = fetcher('dados').get('data') or []
        cache = {}
        for item in data:
            manga_id = item.get('manga_id')
            if manga_id is None:
                continue
            cache[str(manga_id)] = item

        cls.dataset_cache = cache
        cls.dataset_cache_ts = now
        return cache

    def _get_manga_info(self, manga_id: str) -> Optional[dict]:
        dataset = self._get_dataset(self._request_json)
        info = dataset.get(str(manga_id))
        if info:
            return info
        # Força atualização caso não encontrado
        self.__class__.dataset_cache = {}
        dataset = self._get_dataset(self._request_json)
        return dataset.get(str(manga_id))

    def _extract_manga_id(self, link: str) -> str:
        match = re.search(r'/manga/(?:[^/]+/)?(\d+)', link)
        if not match:
            raise ValueError('Não foi possível identificar o ID do mangá na URL informada.')
        return match.group(1)

    def _extract_chapter_id(self, link: str) -> str:
        match = re.search(r'/chapter/(\d+)', link)
        if match:
            return match.group(1)
        # Caso o link seja apenas o ID numérico
        if re.fullmatch(r'\d+', link):
            return link
        raise ValueError('Não foi possível identificar o ID do capítulo na URL informada.')

    def _normalize_image_url(self, url: str) -> str:
        if not url:
            return url
        parsed = urlparse(url)
        if parsed.hostname == 'albums.manhastro.net':
            return f'https://api.manhastro.net/proxy-image{parsed.path}'
        return url

    def _compose_image_urls(self, base_url: str, hash_path: str, data: List[str]) -> List[str]:
        if not base_url or not data:
            return []
        base = base_url.rstrip('/') + '/'
        hash_path = hash_path.strip('/')
        pages = []
        for filename in data:
            filename = str(filename).strip('/')
            segment = '/'.join(filter(None, [hash_path, filename]))
            pages.append(self._normalize_image_url(urljoin(base, segment)))
        return pages

    def _manga_title(self, info: Optional[dict], manga_id: str) -> str:
        if not info:
            return f'Manhastro #{manga_id}'
        return info.get('titulo_brasil') or info.get('titulo') or info.get('nome') or f'Manhastro #{manga_id}'

    def _extract_number_token(self, text: str) -> Optional[str]:
        if not text:
            return None
        matches = re.findall(r'\d+(?:[.,]\d+)?', text)
        if not matches:
            return None
        return matches[-1].replace(',', '.')

    def getManga(self, link: str):
        manga_id = self._extract_manga_id(link)
        info = self._get_manga_info(manga_id)
        title = self._manga_title(info, manga_id)
        manga_link = urljoin(self.url, f'manga/{manga_id}')
        return Manga(id=manga_link, name=title)

    def getChapters(self, id: str) -> List[Chapter]:
        manga_id = self._extract_manga_id(id)
        info = self._get_manga_info(manga_id)
        title = self._manga_title(info, manga_id)
        payload = self._request_json(f'dados/{manga_id}')
        chapters_data = payload.get('data') or []
        chapter_items: List[Tuple[float, Chapter]] = []
        for index, entry in enumerate(chapters_data, start=1):
            chapter_id = entry.get('capitulo_id')
            name = entry.get('capitulo_nome') or f'Capítulo {chapter_id}'
            token = self._extract_number_token(name)
            number = token or str(index)
            try:
                order = float(token) if token is not None else float(index)
            except ValueError:
                order = float(index)
            href = urljoin(self.url, f'manga/{manga_id}/chapter/{chapter_id}')
            chapter_items.append((order, Chapter(id=href, number=str(number), name=title)))

        chapter_items.sort(key=lambda item: item[0])
        return [item[1] for item in chapter_items]

    def getPages(self, ch: Chapter) -> Pages:
        chapter_id = self._extract_chapter_id(ch.id)
        payload = self._request_json(f'paginas/{chapter_id}')
        data = payload.get('data') or {}
        chapter_data = data.get('chapter') or {}

        pages = []
        if isinstance(chapter_data, dict):
            pages = self._compose_image_urls(
                chapter_data.get('baseUrl', ''),
                chapter_data.get('hash', ''),
                chapter_data.get('data') or []
            )

        if not pages:
            paginas_map = data.get('paginas')
            if isinstance(paginas_map, dict):
                pages = [self._normalize_image_url(str(url)) for url in paginas_map.values() if url]

        if not pages:
            raise ValueError('Não foi possível obter as páginas do capítulo no Manhastro.')

        number = self._extract_number_token(str(ch.number)) or ch.number

        return Pages(ch.id, number, ch.name, pages)
    
    def adjust_template_size(self, template, img):
        h_img, w_img = img.shape[:2]
        h_template, w_template = template.shape[:2]

        if h_template > h_img or w_template > w_img:
            scale_h = h_img / h_template
            scale_w = w_img / w_template
            scale = min(scale_h, scale_w)
            template = cv2.resize(template, (int(w_template * scale), int(h_template * scale)))

        return template
    
    def removeMark(self, img_path, template_path, output_path) -> bool:
        img = cv2.imread(img_path)
        template = cv2.imread(template_path)
        template = self.adjust_template_size(template, img)

        h, w = template.shape[:2]

        img_cropped = img[-h:, :]

        result = cv2.matchTemplate(img_cropped, template, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= 0.8:
            img_without_mark = img[:-h, :]

            cv2.imwrite(output_path, img_without_mark)

            return True
        
        return False
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        effective_headers = {}
        if isinstance(self.headers, dict):
            effective_headers.update(self.headers)
        if isinstance(headers, dict):
            effective_headers.update(headers)
        effective_headers.setdefault('Referer', self.url)

        effective_cookies = {}
        base_cookies = self._clone_cookies()
        if isinstance(base_cookies, dict):
            effective_cookies.update(base_cookies)
        if isinstance(cookies, dict):
            effective_cookies.update(cookies)

        pages = DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=effective_headers or None,
            cookies=effective_cookies or None
        )
        marks = ['mark.jpg', 'mark2.jpg', 'mark3.jpg', 'mark4.jpg', 'mark5.jpg', 'mark6.jpg', 'mark7.jpg', 'mark8.jpg', 'mark9.jpg', 'mark10.jpg', 'mark11.jpg']
        for page in pages.files:
            for mark in marks:
                if self.removeMark(page, os.path.join(Path(__file__).parent, mark), page):
                    break
        return  pages
