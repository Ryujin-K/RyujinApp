import re
from typing import List
import nodriver as uc
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Manga, Pages

class EgoToonsProvider(Base):
    name = 'Ego Toons'
    lang = 'pt_Br'
    domain = ['www.egotoons.com']

    def __init__(self) -> None:
        self._base_url = 'https://www.egotoons.com'
        self._api_base = f'{self._base_url}/api'

    def getManga(self, link: str):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')

    def getChapters(self, id: str):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')

    def getPages(self, ch):
        raise NotImplementedError('NekoToonsProvider pending rework after theme deprecation.')