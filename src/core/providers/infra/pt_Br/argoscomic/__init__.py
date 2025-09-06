from typing import List
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages
from core.__seedwork.infra.http import Http
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time


class ArgosComicProvider(Base):
    name = "Argos Comic"
    lang = "pt_BR"
    domain = ["argoscomic.com"]

    def __init__(self) -> None:
        self.webBase = "https://argoscomic.com"

    def _extract_id_slug(self, url_or_id) -> tuple[str, str]:

        url_str = str(url_or_id).strip("/")
        parts = url_str.split("/")
        uuid, slug = None, None

        for i, part in enumerate(parts):
            if len(part) == 36 and part.count("-") == 4:
                uuid = part
                if i + 1 < len(parts):
                    slug = parts[i + 1]
                break

        if not uuid or not slug:
            raise ValueError(f"Não foi possível extrair id e slug da URL: {url_or_id}")

        return uuid, slug

    def getManga(self, manga_url: str) -> Manga:

        #print(f"URL: {manga_url}")
        manga_id, slug = self._extract_id_slug(manga_url)
        #print(f"ID extraído: {manga_id}")
        #print(f"Slug extraído: {slug}")

        name = slug.replace("-", " ").title()
        #print(f"Nome gerado: {name}")

        manga_id_with_slug = f"{manga_id}/{slug}"

        return Manga(id=manga_id_with_slug, name=name)

    def getChapters(self, id: str) -> List[Chapter]:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        uuid, slug = id.split("/", 1)
        url_chapters = f"{self.webBase}/{uuid}/{slug}"

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1400,1000")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

        driver = webdriver.Chrome(options=options)
        driver.get(url_chapters)

        # scroll
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # coleta os capítulos
        chapter_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/capitulo/']")
        chapters = []
        for link in chapter_links:
            try:
                chapter_url = link.get_attribute("href")
                if "/capitulo/" in chapter_url:
                    number = chapter_url.rstrip("/").split("/")[-1]
                    chapters.append(Chapter(id=chapter_url, name=f"Capítulo {number}", number=number))
            except:
                continue

        driver.quit()

        # remove duplicados e ordena
        unique_chapters = {ch.id: ch for ch in chapters}
        chapters = list(unique_chapters.values())
        chapters.sort(key=lambda c: int(c.number))
        return chapters

    def getPages(self, ch: Chapter) -> Pages:

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1400,1000")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

        driver = webdriver.Chrome(options=options)
        driver.get(ch.id)
        time.sleep(2)

        # fechar tuto
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(text(),'Pular tutorial')]")
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
        except:
            pass

        # coleta imagens
        images = []
        page_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-page-index]")
        total_pages = len(page_divs)

        for i in range(total_pages):
            try:
                div = driver.find_element(By.CSS_SELECTOR, f'div[data-page-index="{i}"]')
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", div)
                time.sleep(0.3)
                img = div.find_element(By.TAG_NAME, "img")
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src and "supabase.argoscomic.com" in src:
                    images.append(src)
            except:
                continue

        driver.quit()
        return Pages(id=ch.id, number=ch.number, name=ch.name, pages=images)
