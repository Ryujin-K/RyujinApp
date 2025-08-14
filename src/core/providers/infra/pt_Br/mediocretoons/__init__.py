import requests
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages



class MediocreToonsProvider(Base):
    name = "Mediocre Toons"
    lang = "pt_Br"
    domain = ["mediocretoons.com", "www.mediocretoons.com"]

    def __init__(self) -> None:
        self.base = "https://api.mediocretoons.com"
        self.cdn = "https://storage.mediocretoons.com"
        self.webBase = "https://mediocretoons.com"

    def _get_json(self, url: str) -> dict:
        """Faz uma requisição GET para a URL e retorna os dados JSON."""
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Origin': self.webBase,
            'Referer': f'{self.webBase}/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao acessar a API: {str(e)}")

    def getManga(self, manga_url: str) -> Manga:
        manga_id = manga_url.strip("/").split("/")[-2]  # último segmento é o ID
        data = self._get_json(f"{self.base}/obras/{manga_id}")

        return Manga(
            id=data["id"],
            name=data["nome"]
        )

    def getChapters(self, manga_url: str) -> list[Chapter]:
        manga_id = manga_url.strip("/").split("/")[-2]
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
