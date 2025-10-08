import time
import atexit
import nodriver as uc
import asyncio
import threading
from bs4 import BeautifulSoup
from typing import List
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.wordpress_etoshore_manga_theme import WordpressEtoshoreMangaTheme

_browsers = []
_lock = threading.Lock()
_loop = None
_loop_thread = None

def _get_loop():
    global _loop, _loop_thread
    if _loop is None or _loop.is_closed():
        def run_loop():
            global _loop
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            _loop.run_forever()
        
        _loop_thread = threading.Thread(target=run_loop, daemon=True)
        _loop_thread.start()
        time.sleep(0.5)  # espera loop iniciar
    return _loop

def _run_async(coro):
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)

async def _create_browser():
    return await uc.start(
        headless=True,
        sandbox=False,
        browser_args=['--disable-gpu', '--disable-images', '--no-first-run']
    )

def _get_browser():
    with _lock:
        if _browsers:
            return _browsers.pop()
        return _run_async(_create_browser())

def _return_browser(browser):
    with _lock:
        if len(_browsers) < 3:  # Max 3 no pool
            _browsers.append(browser)
        else:
            _run_async(browser.stop())

def _cleanup():
    global _loop
    with _lock:
        if _browsers:
            async def close_all():
                for browser in _browsers:
                    await browser.stop()
            try:
                _run_async(close_all())
            except:
                pass
            _browsers.clear()
    
    if _loop and not _loop.is_closed():
        _loop.call_soon_threadsafe(_loop.stop)

atexit.register(_cleanup)

class ArgosComicProviderCompact(WordpressEtoshoreMangaTheme):
    name = 'Argos Comic Compact'
    lang = 'pt_Br'
    domain = ['argoscomic.com']

    def __init__(self):
        self.url = 'https://argoscomic.com'
        self.link = 'https://argoscomic.com/'
        self.get_title = 'h1.text-2xl'
        self.get_chapters_list = 'div.space-y-6'
        self.chapter = 'a'
        self.get_chapter_number = 'span.font-medium'
        self.get_pages = 'img'

    async def _get_page_html(self, browser, url):
        page = await browser.get(url)
        await page.sleep(2)
        return await page.get_content()

    async def _click_button(self, browser, text):
        try:
            page = browser.main_tab
            script = f"""
            const buttons = Array.from(document.querySelectorAll('button'));
            const button = buttons.find(b => b.textContent.includes('{text}'));
            if (button) {{ button.click(); return true; }}
            return false;
            """
            return await page.evaluate(script)
        except:
            return False

    async def _expand_volumes(self, browser):
        try:
            page = browser.main_tab
            script = """
            const volumes = document.querySelectorAll('h2');
            let expanded = 0;
            volumes.forEach(vol => {
                if (vol.textContent.match(/Volume|Temporada|Season|Arco|Parte/)) {
                    const svg = vol.closest('div').querySelector('svg path[d^="M17.919"]');
                    if (svg) {
                        vol.closest('div').click();
                        expanded++;
                    }
                }
            });
            return expanded;
            """
            return await page.evaluate(script)
        except:
            return 0

    async def _scroll_page(self, browser):
        try:
            page = browser.main_tab
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.evaluate("""
                document.querySelectorAll('*').forEach(el => {
                    const style = getComputedStyle(el);
                    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                        el.scrollTop = el.scrollHeight;
                    }
                });
            """)
            await page.sleep(1)
        except:
            pass

    def getManga(self, link: str) -> Manga:
        browser = _get_browser()
        try:
            async def get_manga():
                html = await self._get_page_html(browser, link)
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.select_one(self.get_title)
                return title.get_text().strip() if title else "Título não encontrado"
            
            title = _run_async(get_manga())
            return Manga(link, title)
        finally:
            _return_browser(browser)

    def getChapters(self, id: str) -> List[Chapter]:
        browser = _get_browser()
        try:
            async def get_chapters():
                page = await browser.get(id)
                await page.sleep(2)
                
                clicked = await self._click_button(browser, 'Carregar mais capítulos')
                if clicked:
                    await page.sleep(3)
                
                await self._expand_volumes(browser)
                await page.sleep(1)
                
                return await page.get_content()
            
            html = _run_async(get_chapters())
            soup = BeautifulSoup(html, 'html.parser')
            
            chapters_list = soup.select_one(self.get_chapters_list)
            if not chapters_list:
                return []
            
            chapters = chapters_list.select(self.chapter)
            title_elem = soup.select_one(self.get_title)
            title = title_elem.get_text().strip() if title_elem else "Título não encontrado"
            
            result = []
            for ch in chapters:
                number_elem = ch.select_one(self.get_chapter_number)
                if number_elem:
                    href = ch.get('href', '')
                    chapter_url = f"{self.url}{href}" if href.startswith('/') else href
                    result.append(Chapter(chapter_url, number_elem.get_text().strip(), title))
            
            return result
        finally:
            _return_browser(browser)

    def getPages(self, ch: Chapter) -> Pages:
        browser = _get_browser()
        try:
            async def get_pages():
                page = await browser.get(ch.id)
                await page.sleep(2)
                await self._scroll_page(browser)
                return await page.get_content()
            
            html = _run_async(get_pages())
            soup = BeautifulSoup(html, 'html.parser')
            
            img_urls = []
            for img in soup.find_all(self.get_pages):
                src = img.get('src')
                if src:
                    img_urls.append(src)
            
            return Pages(ch.id, ch.number, ch.name, img_urls)
        finally:
            _return_browser(browser)

    @staticmethod
    def close_all():
        _cleanup()

    @staticmethod
    def get_status():
        with _lock:
            return {
                "browsers_in_pool": len(_browsers),
                "loop_running": _loop is not None and _loop.is_running()
            }