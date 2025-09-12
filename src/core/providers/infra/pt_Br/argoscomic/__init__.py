from typing import List
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages
import nodriver as uc
import asyncio
import re
import traceback

class ArgosComicProvider(Base):
    name = "Argos Comic"
    lang = "pt_BR"
    domain = ["argoscomic.com"]

    def __init__(self) -> None:
        self.base = "https://argoscomic.com"

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
        manga_id, slug = self._extract_id_slug(manga_url)
        name = slug.replace("-", " ").title()
        manga_id_with_slug = f"{manga_id}/{slug}"
        return Manga(id=manga_id_with_slug, name=name)

    async def _fetch_chapters(self, url_chapters: str) -> List[Chapter]:
        browser = await uc.start(headless=True)
        try:
            page = await browser.get(url_chapters)

            # wait until 'body'
            for _ in range(50):
                try:
                    body_exists = await page.evaluate("() => !!document.body")
                except Exception:
                    body_exists = False
                if body_exists:
                    break
                await asyncio.sleep(0.1)

            last_height = -1
            for _ in range(40):
                try:
                    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight)")
                    await asyncio.sleep(0.8)
                    new_height = await page.evaluate("() => document.body ? Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) : 0")
                except Exception:
                    break
                if new_height == last_height:
                    break
                last_height = new_height

            try:
                hrefs = await page.evaluate(
                    """() => Array.from(document.querySelectorAll("a[href*='/capitulo/']))
                                    .map(a => a.href)
                                    .filter(h => !!h) || []"""
                ) or []
            except Exception:
                hrefs = []

            if not hrefs:
                try:
                    hrefs = await page.evaluate(
                        """() => Array.from(document.querySelectorAll("a"))
                                        .map(a => a.href)
                                        .filter(h => h && h.includes('/capitulo/')) || []"""
                    ) or []
                except Exception:
                    hrefs = []

            if not hrefs:
                print(" no caps prob selector ")

            seen = set()
            unique = []
            for h in hrefs:
                if h and h not in seen:
                    seen.add(h)
                    unique.append(h)

            chapters = []
            for href in unique:
                number = href.rstrip("/").split("/")[-1]
                chapters.append(Chapter(id=href, name=f"Capítulo {number}", number=number))

            def sort_key(c: Chapter):
                try:
                    return int(c.number)
                except Exception:
                    m = re.search(r"\d+", str(c.number))
                    if m:
                        return int(m.group())
                    return float("inf")

            chapters.sort(key=sort_key)
            return chapters

        except Exception as e:
            print("Erro em _fetch_chapters:", str(e))
            print(traceback.format_exc())
            raise
        finally:
            try:
                await browser.stop()
            except Exception:
                pass

    def getChapters(self, id: str) -> List[Chapter]:
        uuid, slug = id.split("/", 1)
        url_chapters = f"{self.base}/{uuid}/{slug}"
        return asyncio.run(self._fetch_chapters(url_chapters))


    async def _fetch_pages(self, ch: Chapter) -> Pages:
        browser = await uc.start(headless=True)
        page = await browser.get(ch.id)
        await asyncio.sleep(2)

        try:
            btn = await page.select("button:contains('Pular tutorial')")
            if btn:
                await btn.click()
                await asyncio.sleep(1)
        except:
            pass

        divs = await page.select_all("div[data-page-index]")
        images = []
        for i, div in enumerate(divs):
            await div.scroll_into_view()
            await asyncio.sleep(0.3)
            img = await div.select("img")
            if img:
                src = await img.get_attribute("src") or await img.get_attribute("data-src")
                if src and "supabase.argoscomic.com" in src:
                    images.append(src)

        await browser.stop()
        return Pages(id=ch.id, number=ch.number, name=ch.name, pages=images)


    def getPages(self, ch: Chapter) -> Pages:
        return asyncio.run(self._fetch_pages(ch))
