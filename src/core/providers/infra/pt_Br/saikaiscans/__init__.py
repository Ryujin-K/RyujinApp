import json
import nodriver as uc
import tldextract
from typing import List, Iterable
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.config.request_data import get_request, insert_request, RequestData
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class SaikaiScansProvider(Base):
    name = 'Saikai Scans'
    lang = 'pt_Br'
    domain = ['saikaiscans.net', 'housesaikai.net']

    def __init__(self) -> None:
        self.url = 'https://housesaikai.net/'
        self.cookies = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        self._load_cached_session()

    def _load_cached_session(self) -> None:
        for domain in self.domain:
            cached = get_request(domain)
            if cached:
                self.headers.update(cached.headers or {})
                self.cookies.update(cached.cookies or {})
                break

    def _persist_session(self, source_url: str | None = None) -> None:
        if not self.cookies:
            return
        domain = self.domain[0]
        if source_url:
            ext = tldextract.extract(source_url)
            if ext.suffix:
                domain = f"{ext.domain}.{ext.suffix}"
        insert_request(RequestData(
            domain=domain,
            headers=self.headers,
            cookies=self.cookies,
        ))
    
    def getManga(self, link: str) -> Manga:
        response = Http.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1')
        if title.span:
            title.span.decompose()
        return Manga(link, title.get_text(strip=True))
    
    def _exec_js(self, script, background, extract_path='__NUXT__.data[0].story.valueOf().data'):
        content= ''
        async def get_script_result():
            nonlocal content
            browser = await uc.start(
                browser_args=[
                    '--window-size=600,600', 
                    f'--app=https://google.com',
                    '--disable-extensions', 
                    '--disable-popup-blocking'
                ],
                browser_executable_path=None,
                headless=background
            )
            page = await browser.get('https://google.com')
            await page.evaluate(f'{script}')
            content = await page.evaluate(f'JSON.stringify({extract_path})')
            browser.stop()
        uc.loop().run_until_complete(get_script_result())
        return content

    def getChapters(self, id: str) -> List[Chapter]:
        response = Http.get(id)
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', text=lambda t: t and "window.__NUXT__" in t)
        json_content = self._exec_js(script_tag.string, True)
        json_content = json.loads(json_content)
        title = json_content['title']
        chapters = []
        for separator in json_content['separators']:
            for release in separator['releases']:
                chapters.append(Chapter(f'{self.url}ler/comics/{json_content['slug']}/{release['id']}/{release['slug']}', release['chapter'], title))      
        return chapters

    def getPages(self, ch: Chapter) -> Pages:
        nuxt_data, soup = self._fetch_nuxt_data_via_http(ch.id)

        pages_list = self._extract_pages_from_nuxt(nuxt_data) if nuxt_data else []

        if not pages_list and soup:
            pages_list = self._extract_pages_from_html(soup)

        if not pages_list:
            pages_list = self._fetch_pages_via_browser(ch)

        if not pages_list:
            raise Exception('Nenhuma página encontrada após processar o capítulo')

        normalized_pages = self._normalize_pages(ch.id, pages_list)

        if not normalized_pages:
            raise Exception('Nenhuma página válida encontrada para download')

        return Pages(ch.id, ch.number, ch.name, normalized_pages)

    def _fetch_nuxt_data_via_http(self, url: str):
        try:
            response = Http.get(url, headers=self.headers or None, cookies=self.cookies or None)
        except Exception:
            return None, None

        self._load_cached_session()

        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', text=lambda t: t and "window.__NUXT__" in t)
        if script_tag is None or not script_tag.string:
            return None, soup

        try:
            nuxt_data_raw = self._exec_js(script_tag.string, True, extract_path='__NUXT__.data[0]')
            nuxt_data = json.loads(nuxt_data_raw) if nuxt_data_raw else None
            return nuxt_data, soup
        except Exception:
            return None, soup

    def _extract_pages_from_nuxt(self, data: dict) -> List[str]:
        if not isinstance(data, dict):
            return []

        targets: Iterable = (
            data.get('release'),
            data.get('chapter'),
            data.get('story'),
            data.get('content'),
            data.get('data'),
        )

        collections = []
        for target in targets:
            if isinstance(target, dict):
                nested_data = target.get('data') if isinstance(target.get('data'), dict) else {}
                nested_value = target.get('value') if isinstance(target.get('value'), dict) else {}
                collections.extend([
                    target.get('pages'),
                    target.get('images'),
                    nested_data.get('pages'),
                    nested_data.get('images'),
                    nested_value.get('pages'),
                    nested_value.get('images'),
                ])

        collections.extend([
            data.get('pages'),
            data.get('images'),
            data.get('gallery'),
        ])

        for collection in collections:
            if isinstance(collection, list) and collection:
                normalized = []
                for entry in collection:
                    url = self._extract_url_from_entry(entry)
                    if url:
                        normalized.append(url)
                if normalized:
                    return normalized

        return []

    def _extract_url_from_entry(self, entry) -> str | None:
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            for key in ('src', 'url', 'original', 'file'):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            sources = entry.get('sources')
            if isinstance(sources, list):
                for source in sources:
                    link = self._extract_url_from_entry(source)
                    if link:
                        return link
        return None

    def _normalize_pages(self, base_url: str, pages: Iterable[str]) -> List[str]:
        normalized_pages = []
        for page in pages:
            if not isinstance(page, str):
                continue
            page = page.strip()
            if not page:
                continue
            if page.startswith('//'):
                page = f'https:{page}'
            elif not page.startswith('http'):
                page = urljoin(base_url, page)
            normalized_pages.append(page)
        return normalized_pages

    def _extract_pages_from_html(self, soup: BeautifulSoup) -> List[str]:
        selectors = ['#comic-pages', '.reading-content', 'main', '.reader-area', '.chapter-content']
        for selector in selectors:
            container = soup.select_one(selector)
            if not container:
                continue
            candidates = []
            for img in container.select('img, source'):
                attrs = [
                    img.get('src'),
                    img.get('data-src'),
                    img.get('data-lazy-src'),
                    img.get('data-original'),
                ]
                srcset = img.get('srcset') or img.get('data-srcset')
                if srcset:
                    attrs.extend([src.strip().split(' ')[0] for src in srcset.split(',') if src.strip()])
                for attr in attrs:
                    if attr:
                        candidates.append(attr)
                        break
            if candidates:
                return candidates
        return []

    def _fetch_pages_via_browser(self, ch: Chapter) -> List[str]:
        pages_list: List[str] = []

        async def get_pages_from_browser():
            nonlocal pages_list
            browser = await uc.start(
                browser_args=['--window-size=1920,1080'],
                headless=False
            )
            try:
                page = await browser.get(ch.id)

                for _ in range(30):
                    title = await page.evaluate('document.title')
                    safe_title = (title or '').lower()
                    if "momento" not in safe_title and "challenge" not in safe_title:
                        break
                    await page.sleep(1)

                await page.sleep(1)

                for _ in range(15):
                    has_nuxt = await page.evaluate('Boolean(window.__NUXT__?.data?.[0])')
                    if has_nuxt:
                        break
                    await page.sleep(1)

                ua = await page.evaluate('navigator.userAgent')
                if isinstance(ua, str) and ua:
                    self.headers['User-Agent'] = ua

                for cookie in await browser.cookies.get_all():
                    self.cookies[cookie.name] = cookie.value

                try:
                    nuxt_data_raw = await page.evaluate('JSON.stringify(window.__NUXT__?.data?.[0] ?? null)')
                    if nuxt_data_raw and nuxt_data_raw != 'null':
                        nuxt_data = json.loads(nuxt_data_raw)
                        pages_list = self._extract_pages_from_nuxt(nuxt_data)
                except Exception:
                    pages_list = []

                if not pages_list:
                    html = await page.get_content()
                    soup = BeautifulSoup(html, 'html.parser')
                    pages_list = self._extract_pages_from_html(soup)
            finally:
                browser.stop()

        uc.loop().run_until_complete(get_pages_from_browser())

        if pages_list:
            self._persist_session(ch.id)

        return pages_list
    
    def download(self, pages: Pages, fn=None, headers=None, cookies=None):
        from core.download.application.use_cases import DownloadUseCase
        
        cookies = {**self.cookies, **(cookies or {})}

        headers = {**self.headers, **(headers or {})}
        headers.setdefault('Referer', pages.id)
        headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8')
        headers.setdefault('Accept-Language', 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7')
        headers.setdefault('Sec-Fetch-Dest', 'image')
        headers.setdefault('Sec-Fetch-Mode', 'no-cors')
        headers.setdefault('Sec-Fetch-Site', 'same-origin')

        self._persist_session(pages.id)

        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=headers,
            cookies=cookies,
        )

