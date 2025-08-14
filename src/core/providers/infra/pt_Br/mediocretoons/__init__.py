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

    def _extract_id(self, url_or_id) -> str:
        """Extrai o ID numérico da URL (penúltimo segmento)"""
        if isinstance(url_or_id, int):
            return str(url_or_id)
        url_str = str(url_or_id)

        if url_str.isdigit():
            return url_str
        
        parts = url_str.strip("/").split("/")

        if len(parts) >= 2:
            # O penúltimo segmento deve ser o ID
            potential_id = parts[-2]  # Penúltimo elemento
            if potential_id.isdigit():
                return potential_id
        
        raise ValueError(f"Não foi possível extrair o ID da URL: {url_or_id}")

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

    def getManga(self, manga_url_or_id: str) -> Manga:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._get_json(f"{self.base}/obras/{manga_id}")

        return Manga(
            id=data["id"],
            name=data["nome"]
        )

    def getChapters(self, manga_url_or_id: str) -> list[Chapter]:
        manga_id = self._extract_id(manga_url_or_id)
        data = self._get_json(f"{self.base}/obras/{manga_id}")
        chapters = []
        for ch in data.get("capitulos", []):
            chapters.append(Chapter(
                id=str(ch["id"]),
                name=f"Capítulo {ch['numero']}",
                number=str(ch["numero"])
            ))
        return chapters

    def getPages(self, ch: Chapter) -> Pages:
        # Pega dados do capítulo
        chapter_id = ch.id
        data = self._get_json(f"{self.base}/capitulos/{chapter_id}")
        obra_id = str(data["obra"]["id"])
        numero_capitulo = str(data["numero"])
        nome_capitulo = data["nome"]

        # Lista de URLs das imagens, renomeadas como 1,2,3...
        files = [
            f"{self.cdn}/obras/{obra_id}/capitulos/{numero_capitulo}/{p['src']}"
            for p in data.get("paginas", [])
        ]

        # Retorna como Pages do download_entity, com arquivos renomeados
        renamed_files = {str(i+1): url for i, url in enumerate(files)}
        return Pages(
            id=chapter_id,
            number=str(numero_capitulo),
            name=nome_capitulo,
            pages=list(renamed_files.values())
        )


