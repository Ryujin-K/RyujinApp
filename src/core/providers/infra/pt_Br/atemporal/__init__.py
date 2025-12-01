import json
import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Chapter, Pages, Manga
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara

class AtemporalProvider(WordPressMadara):
    name = 'Atemporal'
    lang = 'pt_Br'
    domain = ['atemporal.cloud']

    def __init__(self):
        self.url = 'https://atemporal.cloud'

        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        # Seletores atualizados para a nova estrutura do site
        self.query_chapters = '#chapterlist li a, ul.clstyle li a, div.eplister ul li a, .episodelist ul li a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps, div.page-break, #readerarea img'
        self.query_title_for_uri = 'head meta[property="og:title"], h1.entry-title, div.seriestuheader h1, div.infox h1'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'

        ua = UserAgent()
        user = ua.chrome
        self.headers = {
            'Host': 'atemporal.cloud',
            'User-Agent': user,
            'Referer': f'{self.url}/'
        }
        self.cookies = {'acesso_legitimo': '1'}

    def getManga(self, link: str) -> Manga:
        """Obtém informações do mangá com tratamento robusto para diferentes estruturas de página."""
        uri = urljoin(self.url, link)
        response = Http.get(
            uri,
            headers=self._prepare_headers(referer=uri),
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = None
        
        # Tentar múltiplos seletores para o título
        title_selectors = [
            'head meta[property="og:title"]',
            'h1.entry-title',
            'div.seriestuheader h1',
            'div.infox h1',
            'div.post-title h1',
            'div.post-title h3',
            'title'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                element = elements[0]
                if element.name == 'meta' and 'content' in element.attrs:
                    title = element['content'].strip()
                else:
                    title = element.get_text(strip=True)
                if title:
                    break
        
        # Fallback: extrair título do slug na URL
        if not title:
            from urllib.parse import urlparse
            parsed = urlparse(uri)
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                # Remove prefixo 'manga' se existir e pega o slug
                slug = path_parts[-1] if path_parts[-1] != 'manga' else (path_parts[-2] if len(path_parts) > 1 else 'Unknown')
                title = slug.replace('-', ' ').title()
        
        if not title:
            title = 'Unknown'
        
        return Manga(id=link, name=title)

    def getChapters(self, id: str) -> List[Chapter]:
        uri = urljoin(self.url, id)
        response = Http.get(
            uri,
            headers=self._prepare_headers(referer=uri),
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tentar múltiplos seletores para o título
        title = 'Unknown'
        title_selectors = [
            'head meta[property="og:title"]',
            'h1.entry-title',
            'div.seriestuheader h1',
            'div.infox h1',
            'div.post-title h1',
        ]
        for selector in title_selectors:
            title_nodes = soup.select(selector)
            if title_nodes:
                element = title_nodes[0]
                if element.name == 'meta' and 'content' in element.attrs:
                    title = element['content'].strip()
                else:
                    title = element.get_text(strip=True)
                if title and title != 'Unknown':
                    break

        body_nodes = soup.select('body')
        dom = body_nodes[0] if body_nodes else soup

        # Tentar múltiplos seletores de capítulos
        chapter_selectors = [
            '#chapterlist li a',
            'ul.clstyle li a',
            'div.eplister ul li a',
            '.episodelist ul li a',
            'li.wp-manga-chapter > a',
        ]
        
        data = []
        for selector in chapter_selectors:
            data = dom.select(selector)
            if data:
                break
        
        placeholder = dom.select_one(self.query_placeholder)

        if not data and placeholder:
            try:
                data = self._get_chapters_ajax(id, referer=uri)
            except Exception as ajax_err:
                print(f"[AtemporalProvider] Falha no endpoint AJAX novo: {ajax_err}")
                try:
                    data = self._get_chapters_ajax_old(placeholder['data-id'], referer=uri)
                except Exception as old_ajax_err:
                    print(f"[AtemporalProvider] Falha no endpoint AJAX antigo: {old_ajax_err}")

        chs = []
        for el in data:
            ch_id = self.get_root_relative_or_absolute_link(el, uri)
            if not ch_id:
                continue
            chapter_label = el.select_one('.chapternum, .epl-num, span.chapternum') if hasattr(el, 'select_one') else None
            ch_number = chapter_label.get_text(strip=True) if chapter_label else el.get_text(strip=True)
            ch_name = title
            chs.append(Chapter(ch_id, ch_number, ch_name))

        chs.reverse()
        return chs

    def getPages(self, ch: Chapter) -> Pages:
        uri = urljoin(self.url, ch.id)

        response = Http.get(
            uri,
            headers=self._prepare_headers(referer=uri),
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )

        soup = BeautifulSoup(response.content, 'html.parser')
        script_payload = None
        for script in soup.find_all('script'):
            content = script.string or script.get_text()
            if content and 'ts_reader.run' in content:
                script_payload = content
                break

        if not script_payload:
            print('[AtemporalProvider] Script ts_reader ausente, usando parser padrão')
            return super().getPages(ch)

        match = re.search(r"ts_reader\.run\((\{.*?\})\);", script_payload, re.DOTALL)
        if not match:
            print('[AtemporalProvider] Não foi possível extrair payload ts_reader, usando parser padrão')
            return super().getPages(ch)

        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as err:
            print(f"[AtemporalProvider] Erro ao decodificar payload ts_reader: {err}")
            return super().getPages(ch)

        images = []
        for source in payload.get('sources', []):
            source_images = source.get('images') or []
            if isinstance(source_images, list):
                images.extend(source_images)

        if not images:
            print('[AtemporalProvider] Nenhuma imagem encontrada no payload ts_reader')
            return super().getPages(ch)

        processed = [self.create_connector_uri({'url': image_url, 'referer': uri}) for image_url in images]
        number_match = re.findall(r'\d+\.?\d*', str(ch.number))
        number = number_match[0] if number_match else str(ch.number)
        return Pages(ch.id, number, ch.name, processed)

    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | self.headers
        else:
            headers = self.headers

        provider_cookies = getattr(self, 'cookies', None)
        if cookies is not None and provider_cookies:
            cookies = cookies | provider_cookies
        elif provider_cookies is not None:
            cookies = provider_cookies

        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)