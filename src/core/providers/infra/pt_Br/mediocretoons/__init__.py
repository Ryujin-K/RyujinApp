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

    def getManga(self, nome_obra: str) -> Manga:
        logging.info(f"getManga iniciado para obra: {nome_obra}")

        async def driver():
            browser = await uc.start(
                browser_args=[
                    '--window-size=1200,800',
                    '--disable-extensions',
                    '--disable-popup-blocking'
                ],
                headless=False
            )
            try:
                # 1. Abrir site
                page = await browser.get(self.BASE_WEB)
                logging.debug("Página inicial carregada")

                # 2. Clicar no botão "Todos"
                todos_btn = await page.select("button:has-text('Todos')")
                if todos_btn:
                    await todos_btn[0].click()
                    logging.debug("Botão 'Todos' clicado")
                else:
                    logging.error("Botão 'Todos' não encontrado")
                    return None

                # 3. Buscar no campo de pesquisa
                search_input = await page.select("input[placeholder='Buscar']")
                if search_input:
                    await search_input[0].type(nome_obra)
                    logging.debug(f"Digitado '{nome_obra}' no campo de busca")
                    await asyncio.sleep(1)
                else:
                    logging.error("Campo de busca não encontrado")
                    return None

                # 4. Clicar na obra encontrada
                obra_link = await page.select(f"a:has-text('{nome_obra}')")
                if obra_link:
                    href = await obra_link[0].get_attribute("href")
                    await obra_link[0].click()
                    logging.debug(f"Obra '{nome_obra}' clicada - href: {href}")
                else:
                    logging.error("Obra não encontrada nos resultados")
                    return None

                # 5. Extrair ID da obra da URL
                await asyncio.sleep(1)
                current_url = page.url
                obra_id = self._extract_id(current_url)
                logging.info(f"Obra encontrada: ID={obra_id}, Nome={nome_obra}")

                return Manga(id=obra_id, name=nome_obra)

            finally:
                await browser.stop()

        return uc.loop().run_until_complete(driver())


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

        base_delay = 25
        max_delay = 300
        max_attempts = 5
        attempt = 0
        images = []

        while attempt < max_attempts:
            try:
                current_delay = min(base_delay * math.pow(2, attempt), max_delay)
                logging.info(f"Tentativa {attempt+1}/{max_attempts} - delay {current_delay}s")

                html = self._get_pages_html(
                    url=f"{self.BASE_WEB}/capitulo/{chapter.id}",
                    delay=current_delay,
                    background=attempt > 1
                )

                soup = BeautifulSoup(html, 'html.parser')
                images = [img.get('src') for img in soup.select('img.chakra-image')]

                if images:
                    logging.info(f"Encontradas {len(images)} imagens")
                    break
                else:
                    logging.warning("Nenhuma imagem encontrada, tentando novamente...")
            except Exception as e:
                logging.error(f"Tentativa {attempt+1} falhou: {e}", exc_info=True)

            attempt += 1

        pages = Pages(
            id=chapter.id,
            number=chapter.number,
            name=chapter.name,
            pages=images
        )
        logging.info(f"Pages criado: {pages}")
        return pages
    
    def download(self, pages: Pages, fn: any = None, headers=None, cookies=None):
        logging.info(f"download chamado com Pages: {pages}")
        if headers is None:
            headers = self._default_headers()
        result = DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=headers,
            cookies=cookies
        )
        logging.info(f"download finalizado com resultado: {result}")
        return result
