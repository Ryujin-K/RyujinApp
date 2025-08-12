import nodriver as uc
from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.cloudflare.infra.nodriver.chrome import find_chrome_executable

class MediocreToonsProvider(Base):
    name = 'Mediocretoons'
    lang = 'pt-Br'
    domain = ['mediocretoons.com']
    has_login = False

    def __init__(self) -> None:
        pass   

    def getManga(self, link: str) -> Manga:
        """
        Abre o site, clica no botão 'Todos' e retorna o título do mangá.
        """
        async def _open_and_click_todos():
            browser = await uc.start(
                browser_executable_path=find_chrome_executable(),
                headless=True
            )
            page = await browser.get(link)

            # Aguarda e clica no botão 'Todos'
            xpath_btn_todos = "//button[.//span[text()='Todos']]"
            await page.wait_for_selector(xpath_btn_todos, by="xpath")
            btn_todos = await page.select(xpath_btn_todos, by="xpath")
            if btn_todos:
                await btn_todos[0].click()
                await page.sleep(2)  # Esperar resultados carregarem

            html = await page.get_content()
            browser.stop()
            return html

        # Executa a parte assíncrona
        html = uc.loop().run_until_complete(_open_and_click_todos())
        soup = BeautifulSoup(html, 'html.parser')

        # Agora o título deve estar presente
        title_tag = soup.select_one("h1.text-2xl.font-bold")
        title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

        return Manga(link, title)


    def getChapters(self, manga_url: str) -> List[Chapter]:
        """
        Retorna lista de capítulos disponíveis para o mangá.
        """
        response = Http.get(manga_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        chapters = []
        # Seleciona todos os elementos que contêm o número do capítulo
        chapter_elements = soup.select('div.grow.flex.gap-5 span')

        for ch in chapter_elements:
            chapter_number = ch.get_text(strip=True)
            chapter_url = f"{manga_url}/capitulos/{chapter_number}"
            chapters.append(Chapter(chapter_url, chapter_number, ""))

        return chapters

    def getPages(self, ch: Chapter) -> Pages:
        """
        Abre o capítulo, clica no botão correspondente e retorna as páginas.
        """
        async def _open_and_click():
            browser = await uc.start(
                browser_executable_path=find_chrome_executable(),
                headless=True
            )
            page = await browser.get(ch.id)

            # Aguarda o botão pelo número do capítulo
            xpath_btn = f"//div[contains(@class, 'cursor-pointer')]//span[text()='{ch.number}']"
            await page.wait_for_selector(xpath_btn, by="xpath")

            # Clica no botão
            btn = await page.select(xpath_btn, by="xpath")
            if btn:
                await btn[0].click()
                await page.sleep(2)  # Esperar carregar as imagens

            # Captura HTML final
            html = await page.get_content()
            browser.stop()
            return html

        # Executa parte assíncrona
        html = uc.loop().run_until_complete(_open_and_click())
        soup = BeautifulSoup(html, 'html.parser')

        pages = []
        page_containers = soup.select('div[style*="background: transparent"]')

        for container in page_containers:
            img = container.select_one('img')
            if img and img.get('src'):
                src = img['src']
                if not src.endswith('banner-comeco.JPG') and not src.endswith('banner-fim.JPG'):
                    pages.append(src)

        return Pages(id=ch.id, number=ch.number, name=ch.name, pages=pages)
