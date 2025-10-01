from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent
from core.__seedwork.infra.http import Http
from core.providers.domain.entities import Pages, Chapter, Manga
from core.download.application.use_cases import DownloadUseCase
from core.providers.infra.template.wordpress_madara import WordPressMadara

class HuntersScanProvider(WordPressMadara):
    name = 'Hunters scan'
    lang = 'pt-Br'
    domain = ['hunterscomics.com', 'readhunters.xyz']

    def __init__(self):
        self.url = 'https://readhunters.xyz'
        self.path = ''
        
        self.query_mangas = 'div.post-title h3 a, div.post-title h5 a'
        self.query_chapters = 'li.wp-manga-chapter > a'
        self.query_chapters_title_bloat = None
        self.query_pages = 'div.page-break.no-gaps'
        self.query_title_for_uri = 'head meta[property="og:title"]'
        self.query_placeholder = '[id^="manga-chapters-holder"][data-id]'
        
        ua = UserAgent()
        user = ua.chrome
        self.headers = {
            'User-Agent': user,
            'Referer': f'{self.url}/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Cookie': 'acesso_legitimo=1',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.url,
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.timeout = 10

    def getChapters(self, id: str):
        try:
            uri = urljoin(self.url, id)
            response = Http.get(uri, timeout=self.timeout, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = soup.select(self.query_title_for_uri)
            title = data.pop()['content'].strip() if data else 'Unknown'
            
            placeholder = soup.select_one(self.query_placeholder)
            
            if placeholder:
                return self._get_all_chapters_paginated(id, title)
            else:
                chapters = []
                for el in soup.select(self.query_chapters):
                    ch_id = self.get_root_relative_or_absolute_link(el, uri)
                    chapters.append(Chapter(ch_id, el.text.strip(), title))
                chapters.reverse()
                return chapters
            
        except Exception:
            return []
    
    def _get_all_chapters_paginated(self, manga_id, title):
        """Get all chapters using pagination"""
        if not manga_id.endswith('/'):
            manga_id += '/'
        
        ajax_url = urljoin(self.url, f'{manga_id}ajax/chapters/')
        all_chapters = []
        
        response = Http.post(ajax_url, timeout=self.timeout, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pagination_links = soup.select('a[data-page]')
        max_page = max([int(link.get('data-page', 1)) for link in pagination_links]) if pagination_links else 1
        
        for page in range(1, max_page + 1):
            try:
                if page > 1:
                    response = Http.post(ajax_url, params={'t': page}, timeout=self.timeout, headers=self.headers)
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                for el in soup.select(self.query_chapters):
                    ch_id = self.get_root_relative_or_absolute_link(el, ajax_url)
                    if ch_id:
                        all_chapters.append(Chapter(ch_id, el.text.strip(), title))
                
            except Exception:
                continue
        
        seen = set()
        unique_chapters = [ch for ch in all_chapters if ch.id not in seen and not seen.add(ch.id)]
        unique_chapters.reverse()
        return unique_chapters
    
    def getPages(self, ch: Chapter) -> Pages:
        try:
            urls = self._get_pages_with_browser(ch)
            return Pages(ch.id, ch.number, ch.name, urls)
            
        except Exception as e:
            print(f"getPages error: {e}")
            return Pages(ch.id, ch.number, ch.name, [])
    
    def _get_pages_with_browser(self, ch):
        try:
            import undetected_chromedriver as uc
            import time
            
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-hang-monitor")
            options.add_argument("--disable-prompt-on-repost")
            options.add_argument("--disable-sync")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--no-first-run")
            options.add_argument("--safebrowsing-disable-auto-update")
            options.add_argument("--disable-features=site-per-process,TranslateUI,BlinkGenPropertyTrees")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={self.headers['User-Agent']}")
            
            urls_to_block = [
                "*googlesyndication.com*",
                "*googletagmanager.com*", 
                "*google-analytics.com*",
                "*disable-devtool*",
                "*adblock-checker*",
                "*googleadservices.com*",
                "*doubleclick.net*"
            ]
            
            try:
                driver = uc.Chrome(options=options, version_main=140)  # Chrome 140 based on error
            except Exception:
                driver = uc.Chrome(options=options)
            
            try:
                driver.execute_cdp_cmd('Network.enable', {})
                driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': urls_to_block})
    
                driver.get(ch.id)
                
                script_js = """
                window.originalImageUrls = new Set();
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.initiatorType === 'img' && entry.name.includes('/WP-manga/data/')) {
                            window.originalImageUrls.add(entry.name);
                        }
                    }
                });
                observer.observe({ type: "resource", buffered: true });
                return true;
                """
                
                driver.execute_script(script_js)
                print("Performance Observer configured")
                
                time.sleep(8)
                
                driver.execute_script("""
                    // Scroll to trigger lazy loading
                    window.scrollTo(0, document.body.scrollHeight);
                    window.scrollTo(0, 0);
                    
                    // Trigger events that might load images
                    window.dispatchEvent(new Event('load'));
                    window.dispatchEvent(new Event('DOMContentLoaded'));
                    window.dispatchEvent(new Event('resize'));
                """)
                
                time.sleep(2)
                
                captured_urls = driver.execute_script("return Array.from(window.originalImageUrls);")
                
                if captured_urls:
                    def extract_page_number(url):
                        try:
                            filename = url.split('/')[-1]
                            return int(filename.split('.')[0])
                        except (ValueError, IndexError):
                            return 0
                    
                    sorted_urls = sorted(captured_urls, key=extract_page_number)
                    print(f"Successfully captured {len(sorted_urls)} manga URLs")
                    
                    return sorted_urls
                else:
                    print("No URLs captured")
                    return []
                    
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Selenium error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def download(self, pages: Pages, fn: any, headers=None, cookies=None):
        image_headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': pages.id,
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'acesso_legitimo=1',
            'Origin': self.url,
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        if headers:
            image_headers.update(headers)
        
        return DownloadUseCase().execute(pages=pages, fn=fn, headers=image_headers, cookies=cookies, timeout=self.timeout)