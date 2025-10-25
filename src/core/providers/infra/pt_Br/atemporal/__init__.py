import json
import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Chapter, Pages
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
        self.query_chapters = '#chapterlist li a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'

        ua = UserAgent()
        user = ua.chrome
        self.headers = {
            'Host': 'atemporal.cloud',
            'User-Agent': user,
            'Referer': f'{self.url}/series'
        }
        self.cookies = {'acesso_legitimo': '1'}

    def getChapters(self, id: str) -> List[Chapter]:
        uri = urljoin(self.url, id)
        response = Http.get(
            uri,
            headers=self._prepare_headers(referer=uri),
            cookies=self._clone_cookies(),
            timeout=getattr(self, 'timeout', None)
        )

        soup = BeautifulSoup(response.content, 'html.parser')
        title_nodes = soup.select(self.query_title_for_uri)
        if not title_nodes:
            title = 'Unknown'
        else:
            element = title_nodes.pop()
            title = element['content'].strip() if 'content' in element.attrs else element.text.strip()

        body_nodes = soup.select('body')
        dom = body_nodes[0] if body_nodes else soup

        data = dom.select(self.query_chapters)
        placeholder = dom.select_one(self.query_placeholder)

        if placeholder:
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
            chapter_label = el.select_one('.chapternum') if hasattr(el, 'select_one') else None
            ch_number = chapter_label.text.strip() if chapter_label else el.text.strip()
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