from core.providers.infra.template.base import Base


class NekoToonsProvider(Base):
    name = 'Neko Toons'
    lang = 'pt_Br'
    domain = ['nekotoons.site']

    def __init__(self) -> None:
        self.url = 'https://nekotoons.site'

    def getManga(self, link: str):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')

    def getChapters(self, id: str):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')

    def getPages(self, ch):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')