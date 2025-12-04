import re
import json
from typing import List
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.config.login_data import insert_login, LoginData, get_login, delete_login
from core.config.user_credentials import get_credentials, has_credentials
from core.download.application.use_cases import DownloadUseCase


class KuroMangasProvider(Base):
    name = 'KuroMangas'
    lang = 'pt_Br'
    domain = ['beta.kuromangas.com']
    has_login = True

    def __init__(self) -> None:
        self.api_base = 'https://beta.kuromangas.com/api'
        self.cdn_base = 'https://cdn.kuromangas.com'
        self.web_base = 'https://beta.kuromangas.com'
        self.domain_name = 'beta.kuromangas.com'
        self.access_token = None
        self._load_token()

    def _load_token(self) -> None:
        login_info = get_login(self.domain_name)
        if login_info and login_info.headers.get('authorization'):
            self.access_token = login_info.headers.get('authorization').replace('Bearer ', '')
            print(f"[{self.name}] Token carregado")

    def _save_token(self, token: str) -> None:
        self.access_token = token
        insert_login(LoginData(
            self.domain_name,
            {'authorization': f'Bearer {token}'},
            {}
        ))
        print(f"[{self.name}] Token salvo")

    def requires_credentials(self) -> bool:
        return not has_credentials(self.domain_name)

    def clear_auth(self) -> None:
        self.access_token = None
        delete_login(self.domain_name)
        print(f"[{self.name}] Cache de autenticacao limpo")

    def login(self) -> bool:
        login_info = get_login(self.domain_name)
        if login_info and login_info.headers.get('authorization'):
            print(f"[{self.name}] Login encontrado em cache")
            self._load_token()
            return True

        user_creds = get_credentials(self.domain_name)
        if not user_creds:
            print(f"[{self.name}] Credenciais nao encontradas. Configure pelo menu do app.")
            return False

        print(f"[{self.name}] Realizando login...")

        try:
            login_url = f'{self.api_base}/auth/login'

            payload = {
                "email": user_creds.email,
                "password": user_creds.password
            }

            headers = {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": self.web_base,
                "referer": f"{self.web_base}/login"
            }

            response = Http.post(
                login_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=15
            )

            if response.status in [200, 201]:
                data = response.json()
                access_token = data.get('token') or data.get('access_token') or data.get('accessToken')

                if access_token:
                    self._save_token(access_token)
                    print(f"[{self.name}] Login bem-sucedido!")
                    return True
                else:
                    print(f"[{self.name}] Token nao encontrado na resposta")
                    print(f"[{self.name}] Resposta: {response.content}")
                    return False
            else:
                print(f"[{self.name}] Falha no login - Status: {response.status}")
                print(f"[{self.name}] Resposta: {response.content}")
                return False

        except Exception as e:
            print(f"[{self.name}] Erro ao fazer login: {e}")
            return False

    def _get_headers(self) -> dict:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": self.web_base,
            "referer": f"{self.web_base}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
        if self.access_token:
            headers['authorization'] = f'Bearer {self.access_token}'
        return headers

    def _extract_manga_id(self, link: str) -> str:

        # /manga/1778 ou /reader/1778/195413
        match = re.search(r'/manga/(\d+)', link)
        if match:
            return match.group(1)
        match = re.search(r'/reader/(\d+)/\d+', link)
        if match:
            return match.group(1)
        # apenas número
        if link.isdigit():
            return link
        return link.split('/')[-1]

    def _extract_chapter_id(self, link: str) -> str:

        # /reader/1778/195413
        match = re.search(r'/reader/\d+/(\d+)', link)
        if match:
            return match.group(1)
        # apenas número
        if link.isdigit():
            return link
        return link.split('/')[-1]

    def getManga(self, link: str) -> Manga:
        manga_id = self._extract_manga_id(link)

        try:
            if not self.access_token:
                self.login()

            api_url = f"{self.api_base}/mangas/{manga_id}"
            response = Http.get(api_url, headers=self._get_headers())

            if response.status == 200:
                data = response.json()
                manga_data = data.get('manga', data)
                title = manga_data.get('title', f'Manga {manga_id}')
                return Manga(link, title)
            else:
                print(f"[{self.name}] API retornou {response.status}")
                return Manga(link, f'Manga {manga_id}')
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar manga: {e}")
            return Manga(link, f'Manga {manga_id}')

    def getChapters(self, id: str) -> List[Chapter]:
        manga_id = self._extract_manga_id(id)
        chapters_list = []

        try:
            if not self.access_token:
                self.login()

            api_url = f"{self.api_base}/mangas/{manga_id}"
            response = Http.get(api_url, headers=self._get_headers())

            if response.status != 200:
                print(f"[{self.name}] Erro ao buscar manga: {response.status}")
                return chapters_list

            data = response.json()
            manga_data = data.get('manga', {})
            manga_title = manga_data.get('title', f'Manga {manga_id}')
            chapters = data.get('chapters', [])

            if not chapters:
                print(f"[{self.name}] Nenhum capitulo encontrado")
                return chapters_list

            for ch in chapters:
                ch_id = ch.get('id')
                ch_number = ch.get('chapter_number', '0')
                ch_title = ch.get('title', '')

                try:
                    num_float = float(ch_number)
                    if num_float == int(num_float):
                        formatted_num = str(int(num_float))
                    else:
                        formatted_num = str(ch_number)
                except:
                    formatted_num = str(ch_number)

                if ch_title:
                    cap_name = f"Capítulo {formatted_num} - {ch_title}"
                else:
                    cap_name = f"Capítulo {formatted_num}"

                chapter_url = f"{self.web_base}/reader/{manga_id}/{ch_id}"

                chapter = Chapter(chapter_url, cap_name, manga_title)
                chapter._chapter_id = ch_id
                chapter._manga_id = manga_id

                chapters_list.append(chapter)

            def get_chapter_num(ch):
                match = re.search(r'Capítulo ([\d.]+)', ch.name)
                if match:
                    try:
                        return float(match.group(1))
                    except:
                        return 0
                return 0

            chapters_list.sort(key=get_chapter_num, reverse=True)

            print(f"[{self.name}] Encontrados {len(chapters_list)} capitulos")

        except Exception as e:
            print(f"[{self.name}] Erro ao buscar capitulos: {e}")

        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        chapter_id = self._extract_chapter_id(ch.id)
        pages_list = []

        try:
            if not self.access_token:
                self.login()

            api_url = f"{self.api_base}/chapters/{chapter_id}"
            response = Http.get(api_url, headers=self._get_headers())

            if response.status == 200:
                data = response.json()
                pages = data.get('pages', [])

                for page in pages:
                    # page é algo como "/chapters/hash.webp"
                    if page.startswith('/'):
                        full_url = f"{self.cdn_base}{page}"
                    elif page.startswith('http'):
                        full_url = page
                    else:
                        full_url = f"{self.cdn_base}/{page}"

                    pages_list.append(full_url)

                print(f"[{self.name}] Encontradas {len(pages_list)} paginas")
            else:
                print(f"[{self.name}] Erro ao buscar capitulo: {response.status}")

        except Exception as e:
            print(f"[{self.name}] Erro ao buscar paginas: {e}")

        return Pages(ch.id, ch.number, ch.name, pages_list)

    def download(self, pages: Pages, fn=None, headers=None, cookies=None):
        effective_headers = {}
        if isinstance(headers, dict):
            effective_headers.update(headers)

        effective_headers.setdefault('Referer', f'{self.web_base}/')
        effective_headers.setdefault('Origin', self.web_base)
        effective_headers.setdefault('Accept', 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8')
        effective_headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')

        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=effective_headers,
            cookies=cookies
        )
