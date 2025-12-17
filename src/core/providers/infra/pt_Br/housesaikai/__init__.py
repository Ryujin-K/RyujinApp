import json
import re
from typing import Any, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.__seedwork.infra.http import Http
from core.config.login_data import LoginData, delete_login, get_login, insert_login
from core.config.user_credentials import get_credentials, has_credentials
from core.providers.domain.entities import Chapter, Manga, Pages
from core.providers.infra.template.base import Base


class HouseSaikaiProvider(Base):
    name = 'House Saikai'
    lang = 'pt-Br'
    domain = ['housesaikai.net']
    has_login = True

    def __init__(self) -> None:
        self.url = 'https://housesaikai.net'
        self.login_url = f'{self.url}/login'
        self.domain_name = 'housesaikai.net'

        self.cookies: dict[str, str] = {}
        self.headers: dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        self._load_cached_session()

    def requires_credentials(self) -> bool:
        return not has_credentials(self.domain_name)

    def clear_auth(self) -> None:
        delete_login(self.domain_name)
        self.cookies = {}

    def _load_cached_session(self) -> None:
        cached_login = get_login(self.domain_name)
        if cached_login:
            self.headers.update(cached_login.headers or {})
            self.cookies.update(cached_login.cookies or {})
            return

    def _persist_session(self) -> None:
        if not self.cookies:
            return
        insert_login(LoginData(
            domain=self.domain_name,
            headers=self.headers,
            cookies=self.cookies,
        ))

    def _ensure_logged_in(self, probe_url: Optional[str] = None) -> None:
        probe_url = probe_url or self.url
        try:
            resp = Http.get(probe_url, headers=self.headers or None, cookies=self.cookies or None, timeout=30)
        except Exception:
            if not self.login():
                raise
            return

        content = resp.data or ''
        final_url = (resp.url or '')
        try:
            final_path = urlparse(final_url).path
        except Exception:
            final_path = ''

        is_login_route = (final_path == '/login') or final_url.startswith(self.login_url)
        is_login_ssr = 'routePath:"\\u002Flogin"' in content
        looks_like_login = False
        try:
            soup = BeautifulSoup(content, 'html.parser')
            has_email = soup.select_one(
                'input[type=email], input[name=email], input[autocomplete=email], '
                'input[placeholder*="@"], input[placeholder*="mail"], form input[type=text][placeholder]'
            ) is not None
            has_password = soup.select_one('input[type=password], input[name=password], input[autocomplete=current-password]') is not None
            looks_like_login = bool(has_email and has_password)
        except Exception:
            looks_like_login = False

        if is_login_route or looks_like_login or (is_login_ssr and looks_like_login):
            if not self.login():
                raise Exception(f'[{self.name}] Login necessário. Configure credenciais e tente novamente.')

    def login(self) -> bool:
        creds = get_credentials(self.domain_name)
        if not creds:
            print(f'[{self.name}] Credenciais não configuradas. Configure no app (Configurações → Credenciais).')
            return False

        try:
            import nodriver as uc
        except Exception as e:
            print(f'[{self.name}] nodriver não disponível para login automatizado: {e}')
            return False

        email = creds.email
        password = creds.password

        async def do_login(headless: bool) -> None:
            browser = await uc.start(
                browser_args=[
                    '--window-size=1200,800',
                    '--disable-extensions',
                    '--disable-popup-blocking',
                    '--disable-blink-features=AutomationControlled',
                ],
                headless=headless,
            )
            try:
                page = await browser.get(self.login_url)

                for _ in range(80):
                    count = await page.evaluate("document.querySelectorAll('input').length")
                    if isinstance(count, int) and count > 0:
                        break
                    await page.sleep(0.25)

                for _ in range(30):
                    ready = await page.evaluate(
                        "Boolean((document.querySelector('form input[placeholder*=\"@\"], form input[type=email], form input[name=email], form input[autocomplete=email], form input[type=text][placeholder]') || document.querySelector('input[placeholder*=\"@\"], input[type=email], input[name=email], input[autocomplete=email], input[type=text][placeholder]')) && document.querySelector('input[type=password], input[name=password], input[autocomplete=current-password]'))"
                    )
                    if ready:
                        break
                    await page.sleep(0.5)

                creds_json = json.dumps({'email': email, 'password': password})
                js = (
                    "(() => {"
                    f"const creds = {creds_json};"
                    "const setValue = (el, v) => { if (!el) return; const d = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value'); d && d.set ? d.set.call(el, v) : (el.value = v); el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); };"
                    "const email = document.querySelector('form input[placeholder*=\"@\"], form input[type=email], form input[name=email], form input[autocomplete=email], form input[type=text][placeholder]') || document.querySelector('input[placeholder*=\"@\"], input[type=email], input[name=email], input[autocomplete=email], input[type=text][placeholder]');"
                    "const pass = document.querySelector('input[type=password], input[name=password], input[autocomplete=current-password]');"
                    "if (email) { email.focus(); setValue(email, creds.email); }"
                    "if (pass) { pass.focus(); setValue(pass, creds.password); }"
                    "const btn = document.querySelector('form button[type=submit]') || Array.from(document.querySelectorAll('form button')).find(b => /entrar/i.test((b.textContent||''))) || document.querySelector('button[type=submit]');"
                    "if (btn) btn.click();"
                    "const form = document.querySelector('form');"
                    "if (form && form.requestSubmit) form.requestSubmit();"
                    "if (form && form.submit) form.submit();"
                    "if (pass) { const ev = new KeyboardEvent('keydown', {key:'Enter', code:'Enter', which:13, keyCode:13, bubbles:true}); pass.dispatchEvent(ev); }"
                    "})();"
                )
                await page.evaluate(js)

                logged_in = False
                max_checks = 40 if headless else 240
                sleep_s = 0.5 if headless else 1.0
                for _ in range(max_checks):
                    href = await page.evaluate('location.href')
                    logged_in = await page.evaluate('Boolean(window.__NUXT__?.state?.auth?.loggedIn)')
                    if logged_in or (isinstance(href, str) and '/login' not in href):
                        break
                    await page.sleep(sleep_s)

                href = await page.evaluate('location.href')
                if not logged_in and isinstance(href, str) and '/login' in href:
                    raise Exception('login falhou (permaneceu na página de login)')

                ua = await page.evaluate('navigator.userAgent')
                if isinstance(ua, str) and ua:
                    self.headers['User-Agent'] = ua

                self.cookies = {}
                for cookie in await browser.cookies.get_all():
                    self.cookies[cookie.name] = cookie.value

                if not self.cookies and not logged_in:
                    current_url = await page.evaluate('location.href')
                    raise Exception(f'login não estabeleceu sessão (url={current_url})')

            finally:
                browser.stop()

        try:
            uc.loop().run_until_complete(do_login(headless=True))
        except Exception as e:
            try:
                uc.loop().run_until_complete(do_login(headless=False))
            except Exception as e2:
                print(f'[{self.name}] Falha ao logar via browser: {e2}')
                return False

        if not self.cookies:
            print(f'[{self.name}] Login não retornou cookies; pode ter falhado.')
            return False

        self._persist_session()
        print(f'[{self.name}] Login OK (cookies salvos).')
        return True

    def _extract_pages_from_nuxt(self, data: Any) -> List[str]:
        if not isinstance(data, dict):
            return []
        targets: Iterable[Any] = (
            data.get('release'),
            data.get('chapter'),
            data.get('story'),
            data.get('content'),
            data.get('data'),
        )
        collections: List[Any] = []
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
        collections.extend([data.get('pages'), data.get('images'), data.get('gallery')])
        for collection in collections:
            if isinstance(collection, list) and collection:
                urls: List[str] = []
                for entry in collection:
                    url = self._extract_url_from_entry(entry)
                    if url:
                        urls.append(url)
                if urls:
                    return urls
        return []

    def _extract_url_from_entry(self, entry: Any) -> Optional[str]:
        if isinstance(entry, str) and entry.strip():
            return entry.strip()
        if isinstance(entry, dict):
            for key in ('src', 'url', 'original', 'file'):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            sources = entry.get('sources')
            if isinstance(sources, list):
                for source in sources:
                    link = self._extract_url_from_entry(source)
                    if link:
                        return link
        return None

    def _normalize_pages(self, base_url: str, pages: Iterable[str]) -> List[str]:
        normalized: List[str] = []
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
            normalized.append(page)
        return normalized

    @staticmethod
    def _parse_chapter_number(raw: str) -> str:
        raw = (raw or '').strip()
        if not raw:
            return ''
        match = re.search(r'(\d+(?:[\.,]\d+)?)', raw)
        if not match:
            return raw
        return match.group(1).replace(',', '.')

    def _extract_title_from_soup(self, soup: BeautifulSoup) -> str:
        title_el = soup.select_one('div.__title h1') or soup.find('h1')
        if not title_el:
            return self.name
        if title_el.span:
            title_el.span.decompose()
        title = title_el.get_text(strip=True)
        return title or self.name

    def _extract_chapters_from_soup(self, soup: BeautifulSoup, title: str) -> List[Chapter]:
        chapters: List[Chapter] = []
        seen: set[str] = set()

        for a in soup.select('ul.__chapters a[href]'):
            href = a.get('href')
            if not href or '/ler/comics/' not in href:
                continue
            link = urljoin(self.url, href)
            if link in seen:
                continue

            number_el = a.select_one('span.__chapters--number')
            number_raw = number_el.get_text(strip=True) if number_el else ''
            number = self._parse_chapter_number(number_raw)

            chapters.append(Chapter(link, number, title))
            seen.add(link)

        def sort_key(chapter: Chapter) -> tuple[int, float, str]:
            try:
                return (0, float(str(chapter.number).strip() or '0'), chapter.id)
            except Exception:
                return (1, 0.0, chapter.id)

        chapters.sort(key=sort_key)
        return chapters

    @staticmethod
    def _walk_json(value: Any) -> Iterable[Any]:
        stack: list[Any] = [value]
        while stack:
            current = stack.pop()
            yield current
            if isinstance(current, dict):
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)

    def _find_story(self, root: Any) -> Optional[dict[str, Any]]:
        for node in self._walk_json(root):
            if isinstance(node, dict):
                if isinstance(node.get('separators'), list) or isinstance(node.get('releases'), list):
                    return node
        return None

    def _collect_releases(self, story: dict[str, Any]) -> list[dict[str, Any]]:
        releases: list[dict[str, Any]] = []
        for source in (story.get('separators'), story.get('releases')):
            if isinstance(source, list):
                for item in source:
                    if isinstance(item, dict):
                        rels = item.get('releases') if isinstance(item.get('releases'), list) else None
                        if rels:
                            releases.extend([r for r in rels if isinstance(r, dict)])
                        elif 'slug' in item or 'id' in item:
                            releases.append(item)
        if not releases:
            found = self._find_story({'root': story})
            if isinstance(found, dict):
                direct = found.get('releases')
                if isinstance(direct, list):
                    releases.extend([r for r in direct if isinstance(r, dict)])
        uniq: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any]] = set()
        for rel in releases:
            key = (rel.get('id'), rel.get('slug'))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(rel)
        return uniq

    def _parse_story_from_soup(self, soup: BeautifulSoup) -> Optional[dict[str, Any]]:
        script = soup.find('script', string=lambda t: t and 'window.__NUXT__' in t)
        if not script or not script.string:
            return None
        nuxt = self._parse_nuxt_script(script.string)
        if isinstance(nuxt, dict):
            for key in ('data', 'state'):
                node = nuxt.get(key)
                if isinstance(node, list) and node:
                    candidate = self._find_story(node[0])
                    if candidate:
                        return candidate
                if isinstance(node, dict):
                    candidate = self._find_story(node)
                    if candidate:
                        return candidate
        return None

    def _load_nuxt_with_browser(self, url: str) -> Optional[Any]:
        try:
            import nodriver as uc
        except Exception:
            return None

        nuxt_json: Optional[str] = None

        async def run() -> None:
            nonlocal nuxt_json
            start_kwargs: dict[str, Any] = {
                'headless': True,
                'browser_args': [
                    '--window-size=1200,800',
                    '--disable-extensions',
                    '--disable-popup-blocking',
                ],
            }
            try:
                from core.cloudflare.infra.nodriver.chrome import find_chrome_executable

                chrome_path = find_chrome_executable()
                if chrome_path:
                    start_kwargs['browser_executable_path'] = chrome_path
            except Exception:
                pass

            browser = await uc.start(**start_kwargs)
            try:
                page = await browser.get(self.url)
                if self.cookies:
                    for name, value in self.cookies.items():
                        if not name or value is None:
                            continue
                        safe_value = str(value).replace('"', '\\"')
                        safe_name = str(name).replace('"', '\\"')
                        await page.evaluate(f'document.cookie = "{safe_name}={safe_value}; path=/; secure; samesite=lax";')
                page = await browser.get(url)
                for _ in range(120):
                    has_nuxt = await page.evaluate('Boolean(window.__NUXT__)')
                    if has_nuxt:
                        break
                    await page.sleep(0.5)
                nuxt_json = await page.evaluate('JSON.stringify(window.__NUXT__)')
            finally:
                browser.stop()

        try:
            uc.loop().run_until_complete(run())
        except Exception:
            return None

        try:
            return json.loads(nuxt_json) if nuxt_json else None
        except Exception:
            return None

    def _build_chapters(self, story: dict[str, Any], title: str, page_url: str) -> List[Chapter]:
        slug = story.get('slug') or story.get('story_slug')
        if not slug:
            try:
                parts = [p for p in urlparse(page_url).path.split('/') if p]
                if len(parts) >= 2 and parts[0] == 'comics':
                    slug = parts[1]
            except Exception:
                slug = None
        releases = self._collect_releases(story)
        chapters: List[Chapter] = []
        for release in releases:
            release_id = release.get('id')
            release_slug = release.get('slug')
            num = release.get('chapter') or release.get('number')
            if release_id and release_slug and slug:
                link = f'{self.url}/ler/comics/{slug}/{release_id}/{release_slug}'
                chapters.append(Chapter(link, str(num or ''), title))
        if chapters:
            def sort_key(ch: Chapter) -> tuple[int, float, str]:
                try:
                    return (0, float(str(ch.number).strip() or '0'), ch.id)
                except Exception:
                    return (1, 0.0, ch.id)
            chapters.sort(key=sort_key)
        return chapters

    def _scrape_chapters_with_browser(self, manga_url: str, title: str) -> List[Chapter]:
        creds = get_credentials(self.domain_name)
        if not creds:
            return []

        try:
            import nodriver as uc
        except Exception:
            return []

        email = creds.email
        password = creds.password
        results: List[Chapter] = []

        async def run() -> None:
            nonlocal results
            start_kwargs: dict[str, Any] = {
                'headless': True,
                'browser_args': [
                    '--window-size=1200,800',
                    '--disable-extensions',
                    '--disable-popup-blocking',
                ],
            }
            try:
                from core.cloudflare.infra.nodriver.chrome import find_chrome_executable

                chrome_path = find_chrome_executable()
                if chrome_path:
                    start_kwargs['browser_executable_path'] = chrome_path
            except Exception:
                pass

            browser = await uc.start(**start_kwargs)
            try:
                page = await browser.get(self.url)
                if self.cookies:
                    for name, value in self.cookies.items():
                        if not name or value is None:
                            continue
                        safe_value = str(value).replace('"', '\\"')
                        safe_name = str(name).replace('"', '\\"')
                        await page.evaluate(
                            f'document.cookie = "{safe_name}={safe_value}; path=/; secure; samesite=lax";'
                        )

                page = await browser.get(manga_url)

                href = await page.evaluate('location.href')
                if isinstance(href, str) and '/login' in href:
                    page = await browser.get(self.login_url)

                for _ in range(60):
                    ready = await page.evaluate(
                        "Boolean((document.querySelector('form input[placeholder*=\"@\"], form input[type=email], form input[name=email], form input[autocomplete=email], form input[type=text][placeholder]') || document.querySelector('input[placeholder*=\"@\"], input[type=email], input[name=email], input[autocomplete=email], input[type=text][placeholder]')) && document.querySelector('input[type=password], input[name=password], input[autocomplete=current-password]'))"
                    )
                    if ready:
                        break
                    await page.sleep(0.5)

                creds_json = json.dumps({'email': email, 'password': password})
                js = (
                    "(() => {"
                    f"const creds = {creds_json};"
                    "const email = document.querySelector('form input[placeholder*=\"@\"], form input[type=email], form input[name=email], form input[autocomplete=email], form input[type=text][placeholder]') || document.querySelector('input[placeholder*=\"@\"], input[type=email], input[name=email], input[autocomplete=email], input[type=text][placeholder]');"
                    "const pass = document.querySelector('input[type=password], input[name=password], input[autocomplete=current-password]');"
                    "if (email) { email.focus(); email.value = creds.email; email.dispatchEvent(new Event('input', {bubbles:true})); email.dispatchEvent(new Event('change', {bubbles:true})); }"
                    "if (pass) { pass.focus(); pass.value = creds.password; pass.dispatchEvent(new Event('input', {bubbles:true})); pass.dispatchEvent(new Event('change', {bubbles:true})); }"
                    "const btn = document.querySelector('button[type=submit]');"
                    "if (btn) btn.click();"
                    "const form = document.querySelector('form');"
                    "if (form) form.submit?.();"
                    "})();"
                )
                await page.evaluate(js)

                for _ in range(90):
                    logged_in = await page.evaluate('Boolean(window.__NUXT__?.state?.auth?.loggedIn)')
                    href = await page.evaluate('location.href')
                    if logged_in or (isinstance(href, str) and '/login' not in href):
                        break
                    await page.sleep(0.5)

                page = await browser.get(manga_url)

                await page.evaluate("document.querySelectorAll('div.__volumes button, div.__volumes a').forEach(b=>b.click())")
                await page.sleep(1.0)
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.sleep(0.6)
                items_json = await page.evaluate(
                    "JSON.stringify(Array.from(document.querySelectorAll('ul.__chapters a[href]')).map(a => ({href: (a.getAttribute('href') || '').trim(), num: (a.querySelector('span.__chapters--number')?.textContent || '').trim()})).filter(x => x.href && x.href.includes('/ler/comics/')))"
                )
                try:
                    items = json.loads(items_json) if isinstance(items_json, str) else []
                except Exception:
                    items = []
                chapter_map: dict[str, str] = {}
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    href = (item.get('href') or '').strip()
                    if not href or '/ler/comics/' not in href:
                        continue
                    link = urljoin(self.url, href)
                    num = self._parse_chapter_number(str(item.get('num') or ''))
                    chapter_map[link] = num
                chapters = [Chapter(link, num, title) for link, num in chapter_map.items()]
                if chapters:
                    def sort_key(ch: Chapter) -> tuple[int, float, str]:
                        try:
                            return (0, float(str(ch.number).strip() or '0'), ch.id)
                        except Exception:
                            return (1, 0.0, ch.id)
                    chapters.sort(key=sort_key)
                    results = chapters
            finally:
                browser.stop()

        try:
            uc.loop().run_until_complete(run())
        except Exception:
            return []

        return results

    def getManga(self, link: str) -> Manga:
        self._ensure_logged_in(link)
        response = Http.get(link, headers=self.headers or None, cookies=self.cookies or None, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = self._extract_title_from_soup(soup)
        return Manga(link, title)

    def getChapters(self, id: str) -> List[Chapter]:
        self._ensure_logged_in(id)

        response = Http.get(id, headers=self.headers or None, cookies=self.cookies or None, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = self._extract_title_from_soup(soup)

        html_chapters = self._extract_chapters_from_soup(soup, title)
        if html_chapters:
            return html_chapters

        story = self._parse_story_from_soup(soup)
        if isinstance(story, dict):
            chapters = self._build_chapters(story, title, id)
            if chapters:
                return chapters

        nuxt_root = self._load_nuxt_with_browser(id)
        if nuxt_root:
            story = self._find_story(nuxt_root)
            if isinstance(story, dict):
                chapters = self._build_chapters(story, title, id)
                if chapters:
                    return chapters

        browser_chapters = self._scrape_chapters_with_browser(id, title)
        if browser_chapters:
            return browser_chapters

        raise Exception(f'[{self.name}] Nenhum capítulo encontrado')

    def getPages(self, ch: Chapter) -> Pages:
        self._ensure_logged_in(ch.id)

        response = Http.get(ch.id, headers=self.headers or None, cookies=self.cookies or None, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', string=lambda t: t and 'window.__NUXT__' in t)
        pages: List[str] = []
        if script_tag and script_tag.string:
            nuxt_data = self._parse_nuxt_script(script_tag.string)
            if isinstance(nuxt_data, dict):
                data_node = None
                for key in ('data', 'state'):
                    node = nuxt_data.get(key)
                    if isinstance(node, list) and node:
                        data_node = node[0]
                        break
                if not data_node and isinstance(nuxt_data.get('data'), dict):
                    data_node = nuxt_data.get('data')
                pages = self._extract_pages_from_nuxt(data_node)
        if not pages:
            nuxt_root = self._load_nuxt_with_browser(ch.id)
            if nuxt_root and isinstance(nuxt_root, dict):
                pages = self._extract_pages_from_nuxt(nuxt_root.get('data', [None])[0] if isinstance(nuxt_root.get('data'), list) else nuxt_root.get('data'))
        if not pages:
            container = soup.select_one('#comic-pages') or soup.select_one('.reading-content') or soup.select_one('main')
            if container:
                pages = [img.get('src') for img in container.select('img') if img.get('src')]

        normalized = self._normalize_pages(ch.id, pages)
        if not normalized:
            raise Exception(f'[{self.name}] Nenhuma página encontrada no capítulo')

        return Pages(ch.id, ch.number, ch.name, normalized)

    def download(self, pages: Pages, fn=None, headers=None, cookies=None):
        from core.download.application.use_cases import DownloadUseCase

        cookies = {**self.cookies, **(cookies or {})}
        headers = {**self.headers, **(headers or {})}
        headers.setdefault('Referer', pages.id)
        headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8')
        headers.setdefault('Accept-Language', 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7')

        self._persist_session()

        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)

    def _parse_nuxt_script(self, script: str) -> Optional[Any]:
        try:
            match = re.search(r'window.__NUXT__\s*=\s*(\{.*?\})(;|\n|$)', script, re.S)
            if not match:
                return None
            return json.loads(match.group(1))
        except Exception:
            return None

