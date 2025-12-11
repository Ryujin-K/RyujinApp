from typing import List
from urllib.parse import urlparse
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga


class HentaiLivreProvider(Base):
    name = 'Hentai Livre'
    lang = 'pt_Br'
    domain = ['hentailivre.com']

    def __init__(self) -> None:
        self.base_url = "https://hentailivre.com"
        self.api_url = "https://api.hentailivre.com"
    
    def getManga(self, link: str) -> Manga:
        """
        Extrai o ID da obra da URL e busca informações na API
        URL exemplo: https://hentailivre.com/obras/1671
        """
        parsed_url = urlparse(link)
        obra_id = parsed_url.path.split('/')[-1]
        
        # Busca os capítulos para obter o título da obra
        response = Http.get(f'{self.api_url}/api/capitulos/obra/{obra_id}')
        response_json = response.json()
        
        if response_json.get('success') and response_json.get('data') and len(response_json['data']) > 0:
            title = response_json['data'][0].get('obra_titulo', 'Desconhecido')
        else:
            title = 'Desconhecido'
        
        return Manga(obra_id, title)

    def getChapters(self, manga_id: str) -> List[Chapter]:
        """
        Busca todos os capítulos da obra via API
        """
        response = Http.get(f'{self.api_url}/api/capitulos/obra/{manga_id}')
        response_json = response.json()
        
        chapters_list = []
        
        if response_json.get('success') and response_json.get('data'):
            title = response_json['data'][0].get('obra_titulo', 'Desconhecido') if len(response_json['data']) > 0 else 'Desconhecido'
            
            for chapter_data in response_json['data']:
                chapter_id = str(chapter_data.get('id'))
                chapter_number = str(chapter_data.get('numero_capitulo', ''))
                chapter_title = chapter_data.get('titulo', f'Capítulo {chapter_number}')
                
                # Armazena o ID do capítulo e link_imgs para uso posterior
                chapters_list.append(
                    Chapter(
                        f"{chapter_id}|{chapter_data.get('link_imgs', '')}",
                        chapter_number,
                        title
                    )
                )
        
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        """
        Extrai as URLs das páginas do capítulo
        O ch.id contém: "chapter_id|link_imgs"
        """
        # Separa o ID do capítulo e os IDs das mensagens
        parts = ch.id.split('|', 1)
        chapter_id = parts[0]
        link_imgs = parts[1] if len(parts) > 1 else ''
        
        pages_list = []
        
        # Se link_imgs for "TELEGRAM_IMAGES" ou null, não há imagens acessíveis
        # Se houver IDs de mensagens separados por \n, monta as URLs
        if link_imgs and link_imgs != 'TELEGRAM_IMAGES' and link_imgs != 'null':
            message_ids = link_imgs.split('\n')
            for message_id in message_ids:
                if message_id.strip():
                    pages_list.append(f"{self.api_url}/cdn/message/{message_id.strip()}")
        
        return Pages(ch.id, ch.number, ch.name, pages_list)
