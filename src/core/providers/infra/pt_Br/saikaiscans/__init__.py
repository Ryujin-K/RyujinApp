import json
import nodriver as uc
from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class SaikaiScansProvider(Base):
    name = 'Saikai Scans'
    lang = 'pt_Br'
    domain = ['saikaiscans.net', 'housesaikai.net']

    def __init__(self) -> None:
        self.url = 'https://housesaikai.net/'
        self.cookies = {}  # cookies após bypassar cf
    
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
        pages_list = []
        
        async def get_pages_from_browser():
            nonlocal pages_list
            browser = await uc.start(
                browser_args=['--window-size=1920,1080'],
                headless=False
            )
            try:
                page = await browser.get(ch.id)
                
                # Aguardar cf passar (até 30s)
                for _ in range(30):
                    title = await page.evaluate('document.title')
                    if "momento" not in title.lower() and "challenge" not in title.lower():
                        break
                    await page.sleep(1)
                
                await page.sleep(3)
                
                # cookies
                for cookie in await browser.cookies.get_all():
                    self.cookies[cookie.name] = cookie.value

                try:
                    pages_list = await page.evaluate('''
                        (() => {
                            if (!window.__NUXT__?.data?.[0]) return null;
                            const data = window.__NUXT__.data[0];
                            return data.release?.pages || data.release?.images || 
                                   data.pages || data.images || null;
                        })()
                    ''') or []
                except:
                    pass
                
                if not pages_list:
                    soup = BeautifulSoup(await page.get_content(), 'html.parser')
                    for selector in ['#comic-pages', '.reading-content', 'main']:
                        if div := soup.select_one(selector):
                            pages_list = [img.get('src') or img.get('data-src') 
                                        for img in div.select('img') 
                                        if img.get('src') or img.get('data-src')]
                            if pages_list:
                                break
            finally:
                browser.stop()
        
        uc.loop().run_until_complete(get_pages_from_browser())
        return Pages(ch.id, ch.number, ch.name, pages_list)
    
    def download(self, pages: Pages, fn=None, headers=None, cookies=None):
        from core.download.application.use_cases import DownloadUseCase
        
        # Combinar cookies existentes com os do cf
        if cookies is None:
            cookies = {}
        cookies.update(self.cookies)
        
        # adicionei headers para evitar 403
        if headers is None:
            headers = {}
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': pages.id,
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
        return DownloadUseCase().execute(
            pages=pages, 
            fn=fn, 
            headers=headers, 
            cookies=cookies
        )

