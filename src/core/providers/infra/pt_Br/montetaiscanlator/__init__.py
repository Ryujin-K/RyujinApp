from core.providers.infra.template.wordpress_madara import WordPressMadara
from core.download.application.use_cases import DownloadUseCase
from core.providers.domain.entities import Pages

class MonteTaiScanlatorProvider(WordPressMadara):
    name = 'Monte Tai Scanlator'
    lang = 'pt_Br'
    domain = ['montetaiscanlator.xyz']

    def __init__(self):
        self.url = 'https://montetaiscanlator.xyz/'

        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        if headers is not None:
            headers = headers | {'Referer': 'https://montetaiscanlator.xyz/'}
        else:
            headers = {'Referer': 'https://montetaiscanlator.xyz/'}
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=headers, cookies=cookies)