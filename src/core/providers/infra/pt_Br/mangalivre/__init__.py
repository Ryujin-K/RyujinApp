from core.providers.infra.template.wordpress_madara import WordPressMadara


class MangaLivreProvider(WordPressMadara):
    name = 'Manga Livre'
    lang = 'pt-Br'
    domain = ['mangalivre.to', 'www.mangalivre.to']

    def __init__(self):
        self.url = 'https://mangalivre.to'

        self.path = ''

        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'div.chapter-box a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break'
        self.query_title_for_uri = 'div.post-title > h1'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
