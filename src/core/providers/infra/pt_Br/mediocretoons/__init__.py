from typing import List
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages
from core.__seedwork.infra.http import Http


class MediocreToonsProvider(Base):
    name = "Mediocre Toons"
    lang = "pt_Br"
    domain = [
        "mediocretoons.site",
        "www.mediocretoons.site",
        "mediocretoons.com",
        "www.mediocretoons.com",
    ]

    def __init__(self) -> None:
        self.api_base_urls = [
            "https://api.mediocretoons.site",
            "https://api.mediocretoons.com",
        ]
        self.base = self.api_base_urls[0]
        self.cdn = "https://cdn.mediocretoons.site"
        self.webBase = "https://mediocretoons.site"

    def _extract_id(self, url_or_id) -> str:
        """Aceita ID numérico, decimal ou string"""
        if isinstance(url_or_id, (int, float)):
            return str(url_or_id)

        url_str = str(url_or_id).strip()
        url_str = url_str.split("?", 1)[0]

        try:
            float(url_str)
            return url_str
        except ValueError:
            pass

        parts = [segment for segment in url_str.strip("/").split("/") if segment]
        for segment in reversed(parts):
            try:
                float(segment)
                return segment
            except ValueError:
                continue

        return url_str

    def _get_json(self, url: str) -> dict:
        """Usa o Http para fazer GET e retorna JSON"""
        headers = {
            "Accept": "application/json",
            "Origin": self.webBase,
            "Referer": f"{self.webBase}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = Http.get(url, headers=headers, timeout=30)
        return response.json()

    def _fetch_api(self, endpoint: str) -> dict:
        """Tenta consumir o endpoint em todas as bases disponíveis"""
        last_error = None
        for base_url in self.api_base_urls:
            try:
                url = f"{base_url}{endpoint}"
                data = self._get_json(url)
                self.base = base_url
                return data
            except Exception as error:
                last_error = error
        if last_error:
            raise last_error
        raise RuntimeError("Nenhuma base da API configurada")

    def getManga(self, manga_url_or_id: str) -> Manga:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._fetch_api(f"/obras/{manga_id}")
        return Manga(id=str(data["id"]), name=data["nome"])

    def getChapters(self, manga_url_or_id: str) -> List[Chapter]:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._fetch_api(f"/obras/{manga_id}")
        manga_name = data["nome"]

        chapters_list = [
            Chapter(
                id=str(ch["id"]),
                name=manga_name,
                number=str(ch["numero"])
            )
            for ch in data.get("capitulos", [])
        ]

        # Ordena: números primeiro (inteiros/decimais), depois strings
        def sort_key(c: Chapter):
            try:
                return (0, float(c.number))  # números
            except ValueError:
                return (1, c.number.lower())  # strings

        chapters_list.sort(key=sort_key)
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        data = self._fetch_api(f"/capitulos/{ch.id}")
        obra_id = str(data["obra"]["id"])
        capitulo_numero = str(data["numero"])

        imagens = [
            f"{self.cdn}/obras/{obra_id}/capitulos/{capitulo_numero}/{p['src']}"
            for p in data.get("paginas", [])
        ]

        return Pages(
            id=str(ch.id),
            number=ch.number,
            name=ch.name,
            pages=imagens
        )
