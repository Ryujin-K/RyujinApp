import re
from typing import List
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
        # sem bloqueios/cookies especiais por enquanto
        self.cookies = []

    # ---------- helpers ----------
    def _extract_obra_id(self, link: str) -> str:
        # ex: https://mediocretoons.com/obra/971/eu-reencarnei...
        m = re.search(r'/obra/(\d+)', link)
        if not m:
            raise ValueError('Não foi possível extrair o ID da obra da URL.')
        return m.group(1)

    # ---------- domínio público ----------
    def getManga(self, link: str) -> Manga:
        obra_id = self._extract_obra_id(link)
        # API obra: https://api.mediocretoons.com/obras/{id}
        resp = Http.get(f'{self.base}/obras/{obra_id}').json()
        # exemplos que você passou:
        # { "id": 971, "nome": "Eu Reencarnei como o Herdeiro Louco", ... }
        title = resp.get('nome') or resp.get('obr_nome')  # tolerante a variação
        return Manga(link, title)

    def getChapters(self, id: str) -> List[Chapter]:
        """
        `id` aqui é a URL pública da obra (mantém compatibilidade com seu fluxo).
        Vamos buscar a obra e tentar ler os capítulos a partir do payload.
        Caso a API não retorne embutido, há dois fallbacks:
          1) tentar endpoint comum /obras/{id}/capitulos
          2) (opcional) scraper — deixado de fora por ora
        """
        obra_id = self._extract_obra_id(id)

        # 1) tentativa pela própria obra
        resp = Http.get(f'{self.base}/obras/{obra_id}').json()

        # normalizamos possíveis chaves
        capitulos = (
            resp.get('capitulos')
            or resp.get('resultado', {}).get('capitulos')
            or []
        )

        # 2) se vier vazio, tenta endpoint dedicado
        if not capitulos:
            try:
                # muitos backends expõem esse padrão
                resp2 = Http.get(f'{self.base}/obras/{obra_id}/capitulos').json()
                # pode vir como lista direta ou como { "capitulos": [...] }
                capitulos = resp2.get('capitulos', resp2) if isinstance(resp2, dict) else resp2
            except Exception:
                capitulos = []

        lista: List[Chapter] = []

        for ch in capitulos:
            # padroniza campos possíveis
            cap_id = ch.get('id') or ch.get('cap_id')
            cap_nome = ch.get('nome') or ch.get('cap_nome') or str(cap_id)
            cap_numero = ch.get('numero') or ch.get('cap_numero') or ch.get('nome')  # alguns sites usam "nome" como número

            # guardamos tudo que precisamos para montar as páginas depois:
            # [obra_id, cap_id, cap_numero]
            lista.append(Chapter([obra_id, cap_id, cap_numero], cap_nome, resp.get('nome') or resp.get('obr_nome')))

        return lista

    def getPages(self, ch: Chapter) -> Pages:
        """
        API capítulo: https://api.mediocretoons.com/capitulos/{cap_id}
        Exemplo que você trouxe:
        {
          "id": 89535,
          "nome": "116",
          "numero": "116",
          "paginas": [{ "src": "281d13....webp" }, ...]
        }
        A URL final da imagem é:
        https://storage.mediocretoons.com/obras/{obra_id}/capitulos/{numero}/{src}
        """
        obra_id, cap_id, cap_numero = ch.id[0], ch.id[1], ch.id[2]
        data = Http.get(f'{self.base}/capitulos/{cap_id}').json()

        numero = data.get('numero') or cap_numero or data.get('nome')
        paginas = data.get('paginas', [])

        # monta URLs absolutas
        images = [
            f"{self.CDN}/obras/{obra_id}/capitulos/{numero}/{p.get('src')}"
            for p in paginas if p.get('src')
        ]

        # fallback (se por algum motivo vierem URLs absolutas no HTML):
        if not images and isinstance(paginas, list):
            # tenta encontrar 'url' direta
            images = [p.get('url') for p in paginas if p.get('url')]

        return Pages(ch.id, ch.number, ch.name, images)
