from core.providers.infra.template.wordpress_madara import WordPressMadara

class SeitaCelestialProvider(WordPressMadara):
    name = 'Seita Celestial'
    lang = 'pt-Br'
    domain = ['seitacelestial.com']

    def __init__(self):
        super().__init__()
        self.url = 'https://seitacelestial.com'
        self.path = ''