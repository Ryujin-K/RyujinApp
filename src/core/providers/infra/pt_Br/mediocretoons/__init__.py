from typing import List
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages
from core.__seedwork.infra.http import Http


class MediocreToonsProvider(Base):
    name = "Mediocre Toons"
    lang = "pt_Br"
    domain = ["mediocretoons.com", "www.mediocretoons.com"]

    def __init__(self) -> None:
        self.base = "https://api.mediocretoons.com"
        self.cdn = "https://storage.mediocretoons.com"
        self.webBase = "https://mediocretoons.com"

    def _extract_id(self, url_or_id) -> str:
        """Extrai o ID numérico da URL (penúltimo segmento)"""
        if isinstance(url_or_id, int):
            return str(url_or_id)
        url_str = str(url_or_id)
        if url_str.isdigit():
            return url_str
        
        parts = url_str.strip("/").split("/")
        if len(parts) >= 2:
            potential_id = parts[-2]
            if potential_id.isdigit():
                return potential_id
        
        raise ValueError(f"Não foi possível extrair o ID da URL: {url_or_id}")

    def _get_json(self, url: str) -> dict:
        """Usa o Http para fazer GET e retorna JSON"""
        headers = {
            "Accept": "application/json",
            "Origin": self.webBase,
            "Referer": f"{self.webBase}/"
        }
        response = Http.get(url, headers=headers, timeout=10)
        return response.json()

    def getManga(self, manga_url_or_id: str) -> Manga:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._get_json(f"{self.base}/obras/{manga_id}")
        return Manga(id=str(data["id"]), name=data["nome"])

    def getChapters(self, manga_url_or_id: str) -> List[Chapter]:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._get_json(f"{self.base}/obras/{manga_id}")
        manga_name = data["nome"]

        chapters_list = []
        for ch in data.get("capitulos", []):
            chapters_list.append(
                Chapter(
                    id=str(ch["id"]),
                    name=manga_name,
                    number=ch["numero"]
                )
            )

        # Ordena pelo número do capítulo
        chapters_list.sort(key=lambda c: int(c.number))
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        data = self._get_json(f"{self.base}/capitulos/{ch.id}")
        obra_id = str(data["obra"]["id"])
        #numero_capitulo = str(data["numero"])
        #nome_capitulo = ch.name
        #nome_obra = ch.name

        imagens = [
            f"{self.cdn}/obras/{obra_id}/capitulos/{ch.number}/{p['src']}"
            for p in data.get("paginas", [])
        ]

        return Pages(
            id=str(ch.id),
            number=ch.number,
            name=ch.name,
            pages=imagens
        )
