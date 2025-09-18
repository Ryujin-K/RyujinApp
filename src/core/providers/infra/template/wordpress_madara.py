import re
from typing import List
from bs4 import BeautifulSoup
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.__seedwork.infra.http.contract.http import Response
from core.providers.domain.entities import Chapter, Pages, Manga
from core.providers.infra.template.scraper_logger import ScraperLogger
from urllib.parse import urljoin, urlencode, urlparse, urlunparse, parse_qs

class WordPressMadara(Base):
    def __init__(self):
        self.url = None
        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        self.timeout=None
        
        super().__init__()  # Chama o init da base que já faz o log
        ScraperLogger.debug(self.name, "init", "Configurações do Madara", 
                           selectors={
                               "mangas": self.query_mangas,
                               "chapters": self.query_chapters, 
                               "pages": self.query_pages,
                               "title": self.query_title_for_uri
                           })

    def getManga(self, link: str) -> Manga:
        ScraperLogger.info(self.name, "getManga", "Iniciando busca de manga", url=link)
        
        try:
            response = Http.get(link, timeout=getattr(self, 'timeout', None))
            ScraperLogger.http_request(self.name, "GET", link, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            data = soup.select(self.query_title_for_uri)
            ScraperLogger.parsing(self.name, self.query_title_for_uri, len(data), 1)
            
            if not data:
                ScraperLogger.error(self.name, "getManga", "Título não encontrado", 
                                  selector=self.query_title_for_uri)
                raise ValueError("Título do manga não encontrado")
            
            element = data.pop()
            title = element['content'].strip() if 'content' in element.attrs else element.text.strip()
            
            ScraperLogger.success(self.name, "getManga", "Manga encontrado", 
                                title=title, manga_id=link)
            return Manga(id=link, name=title)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getManga", "Falha ao buscar manga", exception=e, url=link)
            raise

    def getChapters(self, id: str) -> List[Chapter]:
        ScraperLogger.info(self.name, "getChapters", "Iniciando busca de capítulos", manga_id=id)
        
        try:
            uri = urljoin(self.url, id)
            ScraperLogger.debug(self.name, "getChapters", "URL construída", full_url=uri)
            
            response = Http.get(uri, timeout=getattr(self, 'timeout', None))
            ScraperLogger.http_request(self.name, "GET", uri, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            data = soup.select(self.query_title_for_uri)
            ScraperLogger.parsing(self.name, self.query_title_for_uri, len(data), 1)
            
            if not data:
                ScraperLogger.warning(self.name, "getChapters", "Título não encontrado, usando ID como fallback")
                title = id
            else:
                element = data.pop()
                title = element['content'].strip() if 'content' in element.attrs else element.text.strip()
                ScraperLogger.debug(self.name, "getChapters", "Título extraído", title=title)
            
            dom = soup.select('body')[0]
            data = dom.select(self.query_chapters)
            ScraperLogger.parsing(self.name, self.query_chapters, len(data), 0, 
                                context="capítulos básicos")
            
            placeholder = dom.select_one(self.query_placeholder)
            if placeholder:
                ScraperLogger.info(self.name, "getChapters", "Detectado sistema AJAX", 
                                 placeholder_id=placeholder.get('data-id'))
                try:
                    data = self._get_chapters_ajax(id)
                    ScraperLogger.success(self.name, "getChapters", "Capítulos AJAX carregados", 
                                        count=len(data))
                except Exception as ajax_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        "Falha no AJAX novo, tentando método antigo", 
                                        error=str(ajax_error))
                    try:
                        data = self._get_chapters_ajax_old(placeholder['data-id'])
                        ScraperLogger.success(self.name, "getChapters", 
                                            "Capítulos AJAX antigo carregados", count=len(data))
                    except Exception as old_ajax_error:
                        ScraperLogger.error(self.name, "getChapters", 
                                          "Falha em ambos métodos AJAX, usando dados estáticos", 
                                          error=str(old_ajax_error))

            chs = []
            for i, el in enumerate(data):
                try:
                    ch_id = self.get_root_relative_or_absolute_link(el, uri)
                    ch_number = el.text.strip()
                    ch_name = title
                    chs.append(Chapter(ch_id, ch_number, ch_name))
                    
                    if i < 3:  # Log apenas os primeiros 3 para não poluir
                        ScraperLogger.debug(self.name, "getChapters", 
                                          f"Capítulo {i+1} processado", 
                                          number=ch_number, ch_id=ch_id[:50] + "...")
                except Exception as ch_error:
                    ScraperLogger.warning(self.name, "getChapters", 
                                        f"Failed to process chapter {i+1}", 
                                        error=str(ch_error), element=str(el)[:100])

            chs.reverse()
            ScraperLogger.success(self.name, "getChapters", "Chapters loaded", 
                                total=len(chs), manga_title=title)
            return chs
            
        except Exception as e:
            ScraperLogger.error(self.name, "getChapters", "Failed to fetch chapters", 
                              exception=e, manga_id=id)
            raise

    def getPages(self, ch: Chapter) -> Pages:
        ScraperLogger.info(self.name, "getPages", "Starting to fetch pages", 
                         chapter=ch.number, chapter_id=ch.id)
        
        try:
            uri = urljoin(self.url, ch.id)
            uri = self._add_query_params(uri, {'style': 'list'})
            ScraperLogger.debug(self.name, "getPages", "URL with style=list parameter", url=uri)
            
            response = Http.get(uri, timeout=getattr(self, 'timeout', None))
            ScraperLogger.http_request(self.name, "GET", uri, response.status)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            data = soup.select(self.query_pages)
            ScraperLogger.parsing(self.name, self.query_pages, len(data), 0, 
                                context="pages with style=list")
            
            if not data:
                ScraperLogger.warning(self.name, "getPages", 
                                    "No pages found with style=list, trying without it")
                uri = self._remove_query_params(uri, ['style'])
                response = Http.get(uri, timeout=getattr(self, 'timeout', None))
                ScraperLogger.http_request(self.name, "GET", uri, response.status)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                data = soup.select(self.query_pages)
                ScraperLogger.parsing(self.name, self.query_pages, len(data), 1, 
                                    context="pages without style=list")
            
            list = [] 
            for i, el in enumerate(data):
                try:
                    page_url = self._process_page_element(el, uri)
                    list.append(page_url)
                    
                    if i < 3:  # Log only the first 3 pages
                        ScraperLogger.debug(self.name, "getPages", 
                                          f"Page {i+1} processed", 
                                          url=page_url[:50] + "...")
                except Exception as page_error:
                    ScraperLogger.warning(self.name, "getPages", 
                                        f"Failed to process page {i+1}", 
                                        error=str(page_error))

            number = re.findall(r'\d+\.?\d*', str(ch.number))[0]
            
            ScraperLogger.success(self.name, "getPages", "Pages loaded", 
                                total=len(list), chapter=ch.number)
            return Pages(ch.id, number, ch.name, list)
            
        except Exception as e:
            ScraperLogger.error(self.name, "getPages", "Failed to fetch pages", 
                              exception=e, chapter=ch.number)
            raise

    def _create_manga_request(self, page):
        form = {
            'action': 'madara_load_more',
            'template': 'madara-core/content/content-archive',
            'page': page,
            'vars[paged]': '0',
            'vars[post_type]': 'wp-manga',
            'vars[posts_per_page]': '250'
        }
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'x-referer': self.url
        }
        request_url = urljoin(self.url, f'{self.path}/wp-admin/admin-ajax.php')
        return Http.post(request_url, data=urlencode(form), headers=headers, timeout=getattr(self, 'timeout', None))

    def _fetch_dom(self, response: Response, query: str):
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.select(query)

    def _get_mangas_from_page(self, page):
        response = self._create_manga_request(page)
        data = self._fetch_dom(response, self.query_mangas)
        return [Manga(id=self.get_root_relative_or_absolute_link(el, response.url), name=el.text.strip()) for el in data]

    def _get_chapters_ajax_old(self, data_id):
        uri = urljoin(self.url, f'{self.path}/wp-admin/admin-ajax.php')
        response = Http.post(uri, data=f'action=manga_get_chapters&manga={data_id}', headers={
            'content-type': 'application/x-www-form-urlencoded',
            'x-referer': self.url
        }, timeout=getattr(self, 'timeout', None))
        data = self._fetch_dom(response, self.query_chapters)
        if data:
            return data
        else:
            raise Exception('No chapters found (old ajax endpoint)!')

    def _get_chapters_ajax(self, manga_id):
        if not manga_id.endswith('/'):
            manga_id += '/'
        uri = urljoin(self.url, f'{manga_id}ajax/chapters/')
        response = Http.post(uri, timeout=getattr(self, 'timeout', None))
        data = self._fetch_dom(response, self.query_chapters)
        if data:
            return data
        else:
            raise Exception('No chapters found (new ajax endpoint)!')

    def _process_page_element(self, element, referer):
        element = element.find('img') or element.find('image')
        src = element.get('data-url') or element.get('data-src') or element.get('srcset') or element.get('src')
        element['src'] = src
        if 'data:image' in src:
            return src.split()[0]
        else:
            uri = urlparse(self.get_absolute_path(element, referer))
            canonical = parse_qs(uri.query).get('src')
            if canonical and canonical[0].startswith('http'):
                uri = uri._replace(query='')
                uri = uri._replace(path=canonical[0])
            return self.create_connector_uri({'url': uri.geturl(), 'referer': referer})

    def _add_query_params(self, url, params):
        url_parts = list(urlparse(url))
        query = dict(parse_qs(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query, doseq=True)
        return urlunparse(url_parts)

    def _remove_query_params(self, url, params):
        url_parts = list(urlparse(url))
        query = dict(parse_qs(url_parts[4]))
        for param in params:
            query.pop(param, None)
        url_parts[4] = urlencode(query, doseq=True)
        return urlunparse(url_parts)

    def get_root_relative_or_absolute_link(self, element, base_url):
        href = element.get('href')
        return urljoin(base_url, href) if href else None

    def get_absolute_path(self, element, base_url):
        return urljoin(base_url, element['src'])

    def create_connector_uri(self, payload):
        return payload['url']
    

