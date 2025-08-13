import json
import requests
import zstandard as zstd
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages



class MediocreToonsProvider(Base):
    name = "Mediocre Toons"
    lang = "pt_BR"
    domain = ["mediocretoons.com", "www.mediocretoons.com"]

    def __init__(self) -> None:
        self.base = "https://api.mediocretoons.com"
        self.cdn = "https://storage.mediocretoons.com"
        self.webBase = "https://mediocretoons.com"

    def _get_json(self, url: str):
        """Faz request e lida com resposta comprimida em zstd"""
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "zstd",
        }
        resp = requests.get(url, headers=headers)

        if resp.headers.get("content-encoding") == "zstd":
            dctx = zstd.ZstdDecompressor()
            reader = dctx.stream_reader(resp.content)
            data = reader.read()
            return json.loads(data.decode("utf-8"))
        else:
            return resp.json()

    def getManga(self, manga_url: str) -> Manga:
        manga_id = manga_url.strip("/").split("/")[-1]  # último segmento é o ID
        data = self._get_json(f"{self.base}/obras/{manga_id}")

        return Manga(
            id=data["id"],
            name=data["nome"]
        )

    def getChapters(self, manga_url: str) -> list[Chapter]:
        manga_id = manga_url.strip("/").split("/")[-1]
        data = self._get_json(f"{self.base}/obras/{manga_id}")

        chapters = []
        for ch in data.get("capitulos", []):
            chapters.append(Chapter(
                id=ch["id"],
                name=f"Capítulo {'numero'}",
                number=ch["numero"]
            ))
        return chapters

    def getPages(self, chapter_url: str) -> list[Pages]:
        chap_id = chapter_url.strip("/").split("/")[-1]
        data = self._get_json(f"{self.base}/capitulos/{chap_id}")

        pages = []
        obra_id = data["obra"]["id"]
        numero_capitulo = data["numero"]
        for p in data.get("paginas", []):
            pages.append(Pages(
                url=f"{self.cdn}/obras/{obra_id}/capitulos/{numero_capitulo}/{p['src']}"
            ))
        return pages
