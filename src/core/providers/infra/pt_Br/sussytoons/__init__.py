import re
import json
import time
from typing import List
from core.__seedwork.infra.http import Http
from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
from core.config.login_data import insert_login, LoginData, get_login, delete_login
from core.config.user_credentials import get_credentials, has_credentials
from core.download.application.use_cases import DownloadUseCase

class SussyToonsProvider(Base):
    name = 'Verdinha'
    lang = 'pt_Br'
    domain = ['verdinha.wtf']
    has_login = True

    def __init__(self) -> None:
        self.api_base = 'https://api.verdinha.wtf'
        self.cdn_base = 'https://cdn.verdinha.wtf'
        self.web_base = 'https://verdinha.wtf'
        self.domain_name = 'verdinha.wtf'
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
                "login": user_creds.email,
                "senha": user_creds.password,
                "tipo_usuario": "usuario"
            }
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "referer": f"{self.web_base}/"
            }
            
            response = Http.post(
                login_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=15
            )
            
            if response.status in [200, 201]:
                data = response.json()
                access_token = data.get('access_token')
                user = data.get('user', {})
                
                if access_token:
                    self._save_token(access_token)
                    print(f"[{self.name}] Login bem-sucedido! Usuario: {user.get('nome', 'Desconhecido')}")
                    return True
                else:
                    print(f"[{self.name}] Token nao encontrado na resposta")
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
            "accept": "application/json",
            "referer": f"{self.web_base}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def _extract_slug(self, link: str) -> str:
        match = re.search(r'/obras?/([^/]+)', link)
        if match:
            return match.group(1)
        return link.split('/')[-1]
    
    def _extract_cap_id(self, link: str) -> str:
        match = re.search(r'/capitulos?/(\d+)', link)
        if match:
            return match.group(1)
        match = re.search(r'/(\d+)/?$', link)
        if match:
            return match.group(1)
        return None

    def getManga(self, link: str) -> Manga:
        slug = self._extract_slug(link)
        
        try:
            if not self.access_token:
                self.login()
            
            api_url = f"{self.api_base}/obras/{slug}"
            response = Http.get(api_url, headers=self._get_headers())
            
            if response.status == 200:
                data = response.json()
                title = data.get('obr_nome', slug)
                return Manga(link, title)
            else:
                print(f"[{self.name}] API retornou {response.status}, usando slug como titulo")
                return Manga(link, slug)
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar manga: {e}")
            return Manga(link, slug)

    def getChapters(self, id: str) -> List[Chapter]:
        slug = self._extract_slug(id)
        chapters_list = []
        
        try:
            if not self.access_token:
                self.login()
            
            obra_url = f"{self.api_base}/obras/{slug}"
            response = Http.get(obra_url, headers=self._get_headers())
            
            if response.status != 200:
                print(f"[{self.name}] Erro ao buscar obra: {response.status}")
                return chapters_list
            
            data = response.json()
            manga_title = data.get('obr_nome', slug)
            obra_id = data.get('obr_id')
            scan_id = data.get('scan_id', 1)
            
            capitulos = data.get('capitulos', [])
            
            if not capitulos:
                print(f"[{self.name}] Nenhum capitulo encontrado")
                return chapters_list
            
            for ch in capitulos:
                cap_id = ch.get('cap_id')
                cap_numero = ch.get('cap_numero', 'N/A')
                cap_nome = ch.get('cap_nome', f'Capitulo {cap_numero}')
                
                chapter_url = f"{self.web_base}/capitulo/{cap_id}"
                
                chapter = Chapter(chapter_url, cap_nome, manga_title)
                chapter._obra_id = obra_id
                chapter._scan_id = scan_id
                chapter._cap_numero = cap_numero
                chapter._cap_id = cap_id
                
                chapters_list.append(chapter)
            
            print(f"[{self.name}] Encontrados {len(chapters_list)} capitulos")
            
        except Exception as e:
            print(f"[{self.name}] Erro ao buscar capitulos: {e}")
        
        return chapters_list

    def getPages(self, ch: Chapter) -> Pages:
        cap_id = self._extract_cap_id(ch.id)
        if not cap_id:
            print(f"[{self.name}] Nao foi possivel extrair cap_id de: {ch.id}")
            return Pages(ch.id, ch.number, ch.name, [])
        
        pages_list = []
        
        try:
            if not self.access_token:
                self.login()
            
            cap_url = f"{self.api_base}/capitulos/{cap_id}"
            response = Http.get(cap_url, headers=self._get_headers())
            
            if response.status == 200:
                cap_data = response.json()
                
                obra_data = cap_data.get('obra', {})
                obra_id = cap_data.get('obr_id') or obra_data.get('obr_id')
                scan_id = obra_data.get('scan_id', 1)
                cap_numero = cap_data.get('cap_numero')
                
                paginas = cap_data.get('cap_paginas', [])
                
                if paginas:
                    timestamp = int(time.time() * 1000)
                    
                    for page in paginas:
                        src = page.get('src')
                        if src:
                            full_url = f"{self.cdn_base}/scans/{scan_id}/obras/{obra_id}/capitulos/{cap_numero}/{src}?_t={timestamp}"
                            pages_list.append(full_url)
                    
                    print(f"[{self.name}] Encontradas {len(pages_list)} paginas")
                else:
                    print(f"[{self.name}] Nenhuma pagina encontrada em cap_paginas")
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
        effective_headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return DownloadUseCase().execute(
            pages=pages,
            fn=fn,
            headers=effective_headers,
            cookies=cookies
        )
