import re
from typing import List
import asyncio
import nodriver as uc
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga

class MediocreToonsProvider(Base):
    name = 'Mediocre Toons'
    lang = 'pt_Br'
    domain = ['mediocretoons.com', 'www.mediocretoons.com']

    def __init__(self) -> None:
        self.base = 'https://api.mediocretoons.com'
        self.CDN = 'https://storage.mediocretoons.com'
        self.webBase = 'https://mediocretoons.com'

    def _extract_obra_id(self, link: str) -> str:
        m = re.search(r'/obra/(\d+)', link)
        if not m:
            raise ValueError('Não foi possível extrair o ID da obra da URL.')
        return m.group(1)

    def getManga(self, link: str) -> Manga:
        obra_id = self._extract_obra_id(link)
        resp = Http.get(f'{self.base}/obras/{obra_id}').json()
        title = resp.get('nome') or resp.get('obr_nome')
        return Manga(link, title)

    def getChapters(self, id: str) -> List[Chapter]:
        obra_id = self._extract_obra_id(id)
        resp = Http.get(f'{self.base}/obras/{obra_id}').json()
        capitulos = resp.get('capitulos') or resp.get('resultado', {}).get('capitulos') or []

        lista: List[Chapter] = []
        for ch in capitulos:
            cap_id = ch.get('id') or ch.get('cap_id')
            cap_nome = ch.get('nome') or ch.get('cap_nome') or str(cap_id)
            cap_numero = ch.get('numero') or ch.get('cap_numero') or ch.get('nome')
            lista.append(Chapter([obra_id, cap_id, cap_numero], cap_nome, resp.get('nome') or resp.get('obr_nome')))
        return lista

    async def _grab_token_cookie(self, chapter_url: str) -> dict:
        browser = await uc.start(headless=True)
        page = await browser.get(chapter_url)
        await asyncio.sleep(3)  # espera carregar o token
        cookies = await browser.cookies.get_all()
        await browser.stop()

        for c in cookies:
            if c['name'].startswith('token_'):
                return {c['name']: c['value']}
        return {}

    def getPages(self, ch: Chapter) -> Pages:
        obra_id, cap_id, cap_numero = ch.id[0], ch.id[1], ch.id[2]
        chapter_url = f"{self.webBase}/obra/{obra_id}/capitulo/{cap_id}"

        # pega o cookie token_* via nodriver
        cookies = uc.loop().run_until_complete(self._grab_token_cookie(chapter_url))

        # usa o cookie na API
        data = Http.get(f'{self.base}/capitulos/{cap_id}', cookies=cookies).json()

        numero = data.get('numero') or cap_numero or data.get('nome')
        images = [
            f"{self.CDN}/obras/{obra_id}/capitulos/{numero}/{p.get('src')}"
            for p in data.get('paginas', []) if p.get('src')
        ]
        return Pages(ch.id, ch.number, ch.name, images)
