from core.providers.infra.template.base import Base
from core.providers.domain.entities import Chapter, Pages, Manga
import re
import json
import html

class EgoToonsProvider(Base):
    name = 'Ego Toons'
    lang = 'pt_Br'
    domain = ['egotoons.com']

    def __init__(self) -> None:
        super().__init__()
        self.base_url = 'https://egotoons.com'
        self.source_path = 'https://cdn.egotoons.com'
        self.manga_sub_string = 'comics'
        self.chapter_sub_string = 'chapter'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _get_json_from_props(self, html: str) -> dict:
        try:
            from bs4 import BeautifulSoup
            import html as html_module
            
            soup = BeautifulSoup(html, 'html.parser')
            app_div = soup.find('div', id='app')
            
            if not app_div or not app_div.get('data-page'):
                return {}
            
            json_str = html_module.unescape(app_div.get('data-page'))
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                cleaned = self._clean_corrupted_json(json_str)
                if cleaned:
                    try:
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        pass
                return self._extract_essential_json_parts(json_str) or {}
                
        except Exception:
            return {}

    def _clean_corrupted_json(self, json_str):
        try:
            import re
            # Remove ads com scripts e patterns comuns de banner
            json_str = re.sub(r'"ads"\s*:\s*\{[^{}]*<script[^>]*>.*?</script>[^{}]*\}', '"ads":{}', json_str, flags=re.DOTALL | re.IGNORECASE)
            for pattern in [r'"home_top"\s*:\s*"[^"]*<script[^"]*"[^"]*"', r'"banner_[^"]*"\s*:\s*"[^"]*<script[^"]*"[^"]*"', r'"ad[^"]*"\s*:\s*"[^"]*<script[^"]*"[^"]*"']:
                json_str = re.sub(pattern, '""', json_str, flags=re.DOTALL | re.IGNORECASE)
            return json_str
        except Exception:
            return None

    def _extract_essential_json_parts(self, json_str):
        try:
            import re
            result = {'props': {}}
            
            component_match = re.search(r'"component"\s*:\s*"([^"]*)"', json_str)
            if component_match:
                result['component'] = component_match.group(1)
            
            for pattern in [r'"comic_infos"\s*:\s*(\{(?:[^{}]++|\{(?:[^{}]++|\{[^{}]*\})*\})*\})', r'"pageProps"\s*:\s*\{[^}]*"comic_infos"\s*:\s*(\{[^}]*\})']:
                match = re.search(pattern, json_str, re.DOTALL)
                if match:
                    try:
                        result['props']['comic_infos'] = json.loads(match.group(1))
                        break
                    except json.JSONDecodeError:
                        continue
            
            return result if result['props'] else None
        except Exception:
            return None

    def _parse_manga_from_json(self, manga_data: dict) -> Manga:
        try:
            # Extrai dados da estrutura comic_infos (padrão do EgoToons)
            comic_data = manga_data.get('comic_infos', manga_data.get('comic', manga_data))
            title = comic_data.get('title', 'Título não encontrado')
            slug = comic_data.get('slug', '')
            
            if '\\u00' in title:
                try:
                    title = json.loads(f'"{title}"')
                except:
                    for old, new in [('\\u00ed', 'í'), ('\\u00e1', 'á'), ('\\u00e9', 'é'), ('\\u00f5', 'õ'), ('\\u00e7', 'ç')]:
                        title = title.replace(old, new)
            
            return Manga(id=slug, name=html.unescape(title))
        except Exception:
            return Manga(id='', name='Erro ao carregar manga')

    def getManga(self, link: str) -> Manga:
        try:
            from core.__seedwork.infra.http import Http
            
            url = f"{self.base_url}/{self.manga_sub_string}/{link}" if not link.startswith('http') else link
            response = Http.get(url, headers=self.headers, timeout=10)
            
            json_data = self._get_json_from_props(response.text())
            props = json_data.get('props', {})
            
            if 'comic_infos' in props:
                return self._parse_manga_from_json({'comic_infos': props['comic_infos']})
            
        except Exception:
            pass
        
        slug = link.split('/')[-1] if '/' in link else link
        return Manga(id=slug, name='Manga não encontrado')

    def _parse_chapters_from_json(self, chapters_data: list, manga_name: str) -> list:
        try:
            chapters = [Chapter(
                id=ch.get('chapter_path') or str(ch.get('id', ch.get('chapter_path', ''))),
                name=manga_name,
                number=str(ch.get('chapter_number', ''))
            ) for ch in chapters_data]
            
            # Ordena
            chapters.sort(key=lambda c: (0, float(c.number)) if c.number.replace('.', '').isdigit() else (1, float('inf')))
            return chapters
        except Exception:
            return []

    def getChapters(self, id: str) -> list:
        try:
            from core.providers.domain.entities import Chapter
            from core.__seedwork.infra.http import Http
            
            url = f"{self.base_url}/{self.manga_sub_string}/{id}"
            response = Http.get(url, headers=self.headers, timeout=10)
            
            json_data = self._get_json_from_props(response.text())
            props = json_data.get('props', {})
            
            if 'comic_infos' in props:
                comic_data = props['comic_infos']
                chapters_data = comic_data.get('chapters', [])
                manga_name = comic_data.get('title', 'Manga')
                
                if '\\u00' in manga_name:
                    try:
                        manga_name = json.loads(f'"{manga_name}"')
                    except:
                        # Fallback manual para caracteres comuns
                        manga_name = manga_name.replace('\\u00ed', 'í').replace('\\u00e1', 'á').replace('\\u00e9', 'é').replace('\\u00f5', 'õ').replace('\\u00e7', 'ç')
                
                manga_name = html.unescape(manga_name)
                
                return self._parse_chapters_from_json(chapters_data, manga_name)
            
            return []
            
        except Exception:
            return []

    def getPages(self, chapter) -> Pages:
        try:
            from core.providers.domain.entities import Pages
            chapter_url = f"{self.base_url}/{self.chapter_sub_string}/{chapter.id}"
            response = self._get_response(chapter_url)
            pages_urls = self._extract_pages_from_corrupted_json(response)
            
            return Pages(
                id=chapter.id,
                number=chapter.number,
                name=chapter.name,
                pages=pages_urls
            )
            
        except Exception:
            return Pages(id=chapter.id, number=chapter.number, name=chapter.name, pages=[])

    def _extract_pages_from_corrupted_json(self, html_content):
        try:
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            app_div = soup.find('div', id='app')
            
            if not app_div or not app_div.get('data-page'):
                return []
            
            pages_match = re.search(r'"pages"\s*:\s*\[((?:[^[\]]+|\[[^\]]*\])*)\]', app_div.get('data-page'), re.DOTALL)
            if not pages_match:
                return []
            
            # Extrai page_paths
            page_paths = re.findall(r'"page_path"\s*:\s*"([^"]*)"', pages_match.group(1))
            if not page_paths:
                return []
            
            # Processa paths e constrói URLs
            def clean_path(path):
                # Remove escapes JSON e limpeza robusta
                clean = path.replace('\\/', '/').replace('\\', '')
                # Remove prefixos "pages/" múltiplos e duplicações
                while clean.startswith('pages/'):
                    clean = clean[6:]
                clean = clean.replace('pages/pages/', '').replace('/pages/', '/')
                # Pega apenas nome do arquivo se ainda há "pages"
                if 'pages' in clean:
                    clean = clean.split('/')[-1].replace('pages', '')
                return clean.split('/')[-1]  # Garante apenas nome do arquivo
            
            page_urls = [f"https://cdn.egotoons.com/image-db/pages/{clean_path(path)}" for path in page_paths]
            
            # Ordena por page_number se disponível
            page_numbers = re.findall(r'"page_number"\s*:\s*"([^"]*)"', pages_match.group(1))
            if len(page_numbers) == len(page_urls):
                numbered_pages = sorted(zip([int(n) for n in page_numbers], page_urls))
                page_urls = [url for _, url in numbered_pages]
            
            return page_urls
            
        except Exception:
            return []

    def _get_response(self, url: str) -> str:
        from core.__seedwork.infra.http import Http
        return Http.get(url, headers=self.headers, timeout=10).text()