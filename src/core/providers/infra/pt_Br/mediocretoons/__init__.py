import re
import json
from typing import List
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Manga, Chapter, Pages
from core.config.login_data import get_login, insert_login, LoginData, delete_login
from core.config.user_credentials import get_credentials, has_credentials


class MediocreToonsProvider(Base):
    name = "Mediocre Toons"
    lang = "pt_Br"
    domain = ["mediocrescan.com"]
    has_login = True

    def __init__(self) -> None:
        self.api_base = "https://api.mediocretoons.site"
        self.cdn = "https://cdn.mediocretoons.site"
        self.web_base = "https://mediocrescan.com"
        self.domain_name = "mediocrescan.com"
        self.access_token = None
        self.cookies = {}
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": self.web_base,
            "referer": f"{self.web_base}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "x-app-key": "toons-mediocre-app"
        }
        
        self._load_token()

    @staticmethod
    def _to_base36(num: int) -> str:
        if num == 0:
            return '0'
        digits = '0123456789abcdefghijklmnopqrstuvwxyz'
        result = []
        while num:
            result.append(digits[num % 36])
            num //= 36
        return ''.join(reversed(result))

    @staticmethod
    def _ot(resource_id: int) -> str:
        salt = "mediocre-work-salt-2024"
        id_str = str(resource_id)
        id_int = int(resource_id)
        id_base36 = MediocreToonsProvider._to_base36(id_int)
        
        combined = f"{id_str}-{salt}"
        a, i = 0, 0
        
        for w, char in enumerate(combined):
            char_code = ord(char)
            a = ((a << 5) - a + char_code) & 0xFFFFFFFF
            i = ((i << 3) - i + char_code + w) & 0xFFFFFFFF
        
        if a > 0x7FFFFFFF:
            a = a - 0x100000000
        if i > 0x7FFFFFFF:
            i = i - 0x100000000
        
        r = MediocreToonsProvider._to_base36(abs(a))[:6]
        d = MediocreToonsProvider._to_base36(abs(i))[:6]
        
        u = ""
        for w in range(8):
            idx = (id_int * (w + 1) * 7) % 26
            u += chr(97 + idx)
        
        parts = [r, u, id_base36, d]
        p = list("".join(parts))
        
        for w in range(len(p) - 1, 0, -1):
            swap_idx = (id_int * 7 + w * 11) % (w + 1)
            p[w], p[swap_idx] = p[swap_idx], p[w]
        
        return "".join(p)[:20]

    @staticmethod
    def _cn(slug: str, max_range: int = 100000) -> int | None:
        if not slug or len(slug) < 4:
            return None
        
        ranges = [(1, 5000), (5001, 50000), (50001, max_range)]
        
        for start, end in ranges:
            for test_id in range(start, end + 1):
                if MediocreToonsProvider._ot(test_id) == slug:
                    return test_id
        
        return None

    def _load_token(self):
        login_info = get_login(self.domain_name)
        if login_info and login_info.headers.get('authorization'):
            self.access_token = login_info.headers.get('authorization').replace('Bearer ', '')
            self.headers['authorization'] = f'Bearer {self.access_token}'
            self.cookies = login_info.cookies if login_info.cookies else {}
            print("[MediocreScans] [OK] Token de acesso carregado")

    def _save_token(self, token: str, cookies: dict = None):
        self.access_token = token
        self.headers['authorization'] = f'Bearer {token}'
        if cookies:
            self.cookies = cookies
        insert_login(LoginData(
            self.domain_name,
            {'authorization': f'Bearer {token}'},
            self.cookies
        ))
        print("[MediocreScans] [OK] Token de acesso salvo")

    def requires_credentials(self) -> bool:
        return not has_credentials(self.domain_name)
    
    def clear_auth(self) -> None:
        self._clear_auth_cache()

    def login(self):
        login_info = get_login(self.domain_name)
        if login_info and login_info.headers.get('authorization'):
            print("[MediocreScans] [OK] Login encontrado em cache")
            self._load_token()
            return True
        
        user_creds = get_credentials(self.domain_name)
        if not user_creds:
            print("[MediocreScans] Credenciais nao encontradas. Configure pelo menu do app.")
            return False
        
        print("[MediocreScans] [LOGIN] Realizando login...")
        
        try:
            login_url = f'{self.api_base}/usuarios/login'
            
            payload = {
                "email": user_creds.email,
                "senha": user_creds.password,
            }
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "origin": self.web_base,
                "referer": f"{self.web_base}/",
                "x-app-key": "toons-mediocre-app"
            }
            
            response = Http.post(
                login_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=15
            )
            
            if response.status in [200, 201]:
                data = response.json()
                
                access_token = data.get('access_token') or data.get('accessToken') or data.get('token')
                user = data.get('user', {}) or data.get('usuario', {})
                
                response_cookies = {}
                if hasattr(response, 'cookies'):
                    response_cookies = dict(response.cookies)
                
                if access_token:
                    self._save_token(access_token, response_cookies)
                    print(f"[MediocreScans] [OK] Login bem-sucedido! Usuário: {user.get('nome', 'Desconhecido')}")
                    return True
                else:
                    print(f"[MediocreScans] [ERRO] Token nao encontrado na resposta")
                    return False
            else:
                print(f"[MediocreScans] [ERRO] Falha no login - Status: {response.status}")
                print(f"[MediocreScans] Resposta: {response.content}")
                return False
                
        except Exception as e:
            print(f"[MediocreScans] [ERRO] Erro ao fazer login: {e}")
            return False

    def _ensure_authenticated(self):
        if not self.access_token:
            self.login()
            return
        
        try:
            test_url = f'{self.api_base}/obras?limite=1'
            response = Http.get(test_url, headers=self.headers, cookies=self.cookies, timeout=10)
            
            if response.status == 401:
                self._clear_auth_cache()
                self.login()
            elif response.status >= 400:
                self._clear_auth_cache()
                self.login()
        except Exception as e:
            self._clear_auth_cache()
            self.login()
    
    def _clear_auth_cache(self):
        self.access_token = None
        self.cookies = {}
        
        if 'authorization' in self.headers:
            del self.headers['authorization']
        
        try:
            delete_login(self.domain_name)
        except Exception as e:
            pass

    def getManga(self, link: str) -> Manga:
        try:
            self._ensure_authenticated()
            
            match = re.search(r'/obra/([^/]+)', link)
            if not match:
                raise Exception("Slug da obra nao encontrado na URL")
                
            slug1 = match.group(1)
            
            print(f"[MediocreScans] Decodificando slug: {slug1}")
            obra_id = self._cn(slug1)
            
            if not obra_id:
                raise Exception(f"Nao foi possivel decodificar o slug: {slug1}")
            
            print(f"[MediocreScans] Slug {slug1} -> ID {obra_id}")
            
            api_url = f'{self.api_base}/obras/{obra_id}'
            print(f"[MediocreScans] Chamando API: {api_url}")
            
            response = Http.get(api_url, headers=self.headers, cookies=self.cookies)
            data = response.json()
            
            title = data.get('nome', 'Titulo Desconhecido')
            return Manga(link, title)
            
        except Exception as e:
            print(f"[MediocreScans] Erro em getManga: {e}")
            raise

    def getChapters(self, manga_id: str) -> List[Chapter]:
        try:
            self._ensure_authenticated()
            
            match = re.search(r'/obra/([^/]+)', manga_id)
            if not match:
                raise Exception("Slug da obra nao encontrado")
                
            slug1 = match.group(1)
            
            print(f"[MediocreScans] Decodificando slug: {slug1}")
            obra_id = self._cn(slug1)
            
            if not obra_id:
                raise Exception(f"Nao foi possivel decodificar o slug: {slug1}")
            
            print(f"[MediocreScans] Slug {slug1} -> ID {obra_id}")
            
            api_url = f'{self.api_base}/obras/{obra_id}'
            print(f"[MediocreScans] Chamando API: {api_url}")
            
            response = Http.get(api_url, headers=self.headers, cookies=self.cookies)
            data = response.json()
            
            title = data.get('nome', 'Titulo Desconhecido')
            chapters_list = []
            
            for ch in data.get('capitulos', []):
                chapters_list.append(Chapter([obra_id, ch['id']], str(ch['numero']), title))
            
            return chapters_list
        except Exception as e:
            print(f"[MediocreScans] Erro em getChapters: {e}")
            return []

    def getPages(self, ch: Chapter) -> Pages:
        self._ensure_authenticated()
        
        images = []
        
        print(f"[MediocreScans] Obtendo paginas para: {ch.name}")
        
        try:
            cap_id = ch.id[1] if isinstance(ch.id, list) else ch.id
            
            api_url = f"{self.api_base}/capitulos/{cap_id}"
            print(f"[MediocreScans] Chamando API: {api_url}")
            
            response = Http.get(api_url, headers=self.headers, cookies=self.cookies)
            data = response.json()
            
            obra_id = data.get('obra', {}).get('id', 'Desconhecido')
            cap_num = data.get('numero', 'Desconhecido')
            
            print(f"[MediocreScans] API retornou {len(data.get('paginas', []))} paginas")

            for i, pagina in enumerate(data.get('paginas', [])):
                try:
                    src = pagina.get('src', '')
                    if src:
                        full_url = f"{self.cdn}/obras/{obra_id}/capitulos/{cap_num}/{src}"
                        if full_url and full_url.startswith('http'):
                            images.append(full_url)
                except Exception as e:
                    continue
            
            if images:
                print(f"[MediocreScans] [OK] Sucesso: {len(images)} paginas encontradas")
                return Pages(ch.id, ch.number, ch.name, images)
            else:
                print("[MediocreScans] Nenhuma pagina valida encontrada")
                
        except Exception as e:
            print(f"[MediocreScans] [ERRO] Erro na API: {e}")

        print("[MediocreScans] [ERRO] Falha na API - retornando lista vazia")
        return Pages(ch.id, ch.number, ch.name, [])

