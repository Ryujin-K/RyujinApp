import logging
import os
import math
import asyncio
from urllib.parse import urlparse
from typing import List
from bs4 import BeautifulSoup
import nodriver as uc

from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.base import Base
from core.download.application.use_cases import DownloadUseCase

# Configurar logging para salvar em arquivo
log_path = os.path.join(os.getcwd(), "mediocretoons_provider.log")
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MediocretoonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt'
    domain = ['mediocretoons.com']
    has_login = False

    BASE_WEB = 'https://mediocretoons.com'
    BASE_API = 'https://api.mediocretoons.com'
    BASE_CDN = 'https://storage.mediocretoons.com/obras'

    def _extract_id(self, url: str) -> str:
        logging.debug(f"_extract_id chamado com URL: {url}")
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] in ['obra', 'obras']:
            logging.debug(f"ID extraído: {parts[1]}")
            return parts[1]
        raise ValueError("URL inválida para extrair ID da obra")
    
    def _default_headers(self):
        logging.debug("_default_headers chamado")
        return {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": self.BASE_WEB,
            "Origin": self.BASE_WEB,
        }

    def getManga(self, obra_nome: str) -> Manga:
        logging.info(f"getManga (Navegação) chamado com obra_nome: {obra_nome}")

        async def driver():
            browser = await uc.start(
                browser_args=[
                    '--window-size=1200,800',
                    '--disable-extensions',
                    '--disable-popup-blocking',
                    '--no-default-browser-check',
                    '--disable-notifications',
                ],
                headless=False  # mude para True depois de testar
            )
            try:
                page = await browser.get(self.BASE_WEB)

                # Espera DOM carregar
                await asyncio.sleep(1.0)

                # Clicar "Todos"
                click_todos_js = """
                (function(){
                    const el = Array.from(document.querySelectorAll('a,button,span,div'))
                      .find(e => (e.textContent || '').trim().toLowerCase() === 'todos');
                    if(el){ el.click(); return true; }
                    return false;
                })();
                """
                await uc.cdp.Runtime.evaluate(
                    page.conn,
                    expression=click_todos_js,
                    returnByValue=True
                )

                await asyncio.sleep(0.6)

                # Digitar no campo de busca
                type_search_js = f"""
                (function(q){{
                    const input = document.querySelector('input[placeholder],input[type="search"]');
                    if(!input) return false;
                    input.focus();
                    input.value = q;
                    input.dispatchEvent(new Event('input', {{bubbles:true}}));
                    input.dispatchEvent(new KeyboardEvent('keydown', {{key:'Enter', bubbles:true}}));
                    return true;
                }})('{obra_nome}');
                """
                await uc.cdp.Runtime.evaluate(
                    page.conn,
                    expression=type_search_js,
                    returnByValue=True
                )

                await asyncio.sleep(1.0)

                # Clicar na obra
                click_obra_js = f"""
                (function(q){{
                    q = q.trim().toLowerCase();
                    const link = Array.from(document.querySelectorAll('a[href^="/obra/"], a[href^="/obras/"]'))
                      .find(a => (a.textContent || '').trim().toLowerCase().includes(q));
                    if(link) {{
                        link.click();
                        return link.href || link.getAttribute('href');
                    }}
                    return null;
                }})('{obra_nome}');
                """
                result = await uc.cdp.Runtime.evaluate(
                    page.conn,
                    expression=click_obra_js,
                    returnByValue=True
                )
                obra_url = result.get("result", {}).get("value")
                await asyncio.sleep(1.0)

                # Pega URL atual se não tiver no click
                if not obra_url:
                    obra_url = await self._run_js(page, "location.href")

                if not obra_url:
                    raise RuntimeError("Não foi possível obter URL da obra.")

                # Extrai ID e consulta API via requests
                obra_id = self._extract_id(obra_url)
                import requests
                url_api = f'{self.BASE_API}/obras/{obra_id}'
                resp = requests.get(url_api, headers=self._default_headers())
                resp.raise_for_status()
                data = resp.json()
                return Manga(id=str(data['id']), name=str(data['nome']))

            finally:
                await browser.stop()

        manga = uc.loop().run_until_complete(driver())
        logging.info(f"Manga criado: {manga}")
        return manga

    def getChapters(self, obra_id: str) -> List[Chapter]:
        logging.info(f"getChapters chamado com obra_id: {obra_id}")
        url = f'{self.BASE_API}/obras/{obra_id}'
        import requests
        resp = requests.get(url, headers=self._default_headers())
        logging.info(f"GET {url} status_code: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"Dados recebidos getChapters: {data}")

        chapters = []
        for ch in data.get('capitulos', []):
            chapter = Chapter(
                id=str(ch['id']),
                number=str(ch.get('numero', None)),
                name=ch.get('nome'),
            )
            chapters.append(chapter)
            logging.info(f"Chapter criado: {chapter}")
        return chapters

    def _get_pages_html(self, url: str, delay: int, background: bool = False) -> str:
        """Usa nodriver para carregar a página e retornar o HTML"""
        async def driver():
            logging.debug(f"Iniciando navegador para {url} com delay {delay}s (background={background})")
            browser = await uc.start(
                browser_args=[
                    '--window-size=600,600',
                    f'--app={url}',
                    '--disable-extensions',
                    '--disable-popup-blocking'
                ],
                headless=background
            )
            try:
                page = await browser.get(url)
                await asyncio.sleep(delay)
                html = await page.get_content()
                return html
            finally:
                logging.debug("Encerrando navegador")
                await browser.stop()

        return uc.loop().run_until_complete(driver())

    def getPages(self, chapter: Chapter) -> Pages:
        logging.info(f"getPages chamado com chapter: {chapter}")
        import requests

        url = f"{self.BASE_API}/capitulos/{chapter.id}"
        resp = requests.get(url, headers=self._default_headers())
        resp.raise_for_status()
        data = resp.json()

        # Aqui as imagens já vêm no JSON
        images = [p['link'] for p in data.get('paginas', [])]

        pages = Pages(
            id=chapter.id,
            number=chapter.number,
            name=chapter.name,
            pages=images
        )
        logging.info(f"Pages criado: {pages}")
        return pages
    

