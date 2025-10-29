import re
import os
import math
from PIL import Image
from io import BytesIO
from core.config.img_conf import get_config
from core.__seedwork.infra.http import Http
from core.providers.domain.page_entity import Pages
from core.download.domain.download_entity import Chapter
from core.download.domain.download_repository import DownloadRepository
from core.__seedwork.infra.utils.sanitize_folder import sanitize_folder_name
Image.MAX_IMAGE_PIXELS = 933120000

class PillowDownloadRepository(DownloadRepository):

    def download(self, pages: Pages, fn=None, headers=None, cookies=None, timeout=None) -> Chapter:
        title = sanitize_folder_name(pages.name)
        config = get_config()
        img_path = config.save
        path = os.path.join(img_path, str(title), str(sanitize_folder_name(pages.number)))
        os.makedirs(path, exist_ok=True)
        img_format = config.img

        page_number = 1
        files = []
        total_pages = len(pages.pages)
        
        if total_pages == 0:
            if fn != None:
                fn(100)
            return Chapter(pages.number, files)
        
        for i, page in enumerate(pages.pages):
            response = Http.get(page, headers=headers, cookies=cookies, timeout=timeout)
            
            original_ext = None
            url_lower = page.lower()
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif', '.bmp']:
                if ext in url_lower:
                    original_ext = ext
                    break
            
            if not original_ext:
                content_type = response.headers.get('content-type', '').lower() if hasattr(response, 'headers') else ''
                ext_map = {
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/png': '.png',
                    'image/webp': '.webp',
                    'image/avif': '.avif',
                    'image/gif': '.gif',
                    'image/bmp': '.bmp'
                }
                original_ext = ext_map.get(content_type, '.jpg')
            
            original_file = os.path.join(path, f"%03d{original_ext}" % page_number)
            
            try:
                img = Image.open(BytesIO(response.content))
                icc = img.info.get('icc_profile')
                
                img.save(original_file, quality=100, dpi=(72, 72), icc_profile=icc)
                
                if img_format.lower() != original_ext.lower():
                    try:
                        if img.mode in ("RGBA", "P") and img_format.lower() in ['.jpg', '.jpeg']:
                            img = img.convert("RGB")
                        
                        converted_file = os.path.join(path, f"%03d{img_format}" % page_number)
                        img.save(converted_file, quality=100, dpi=(72, 72), icc_profile=icc)
                        
                        # Se conversão bem-sucedida, apagar original e usar convertido
                        os.remove(original_file)
                        files.append(converted_file)
                        
                    except Exception as convert_error:
                        # Se conversão falhar, manter original
                        print(f"<stroke style='color:orange;'>[Converting]:</stroke> <span style='color:red;'>Erro ao converter {original_file} para {img_format}: {convert_error}</span>")
                        print(f"<stroke style='color:yellow;'>[Info]:</stroke> Mantendo imagem original: {original_file}")
                        files.append(original_file)
                else:
                    files.append(original_file)
                    
            except Exception as e:
                print(f"<stroke style='color:green;'>[Downloading]:</stroke> <span style='color:red;'>Error ao processar imagem: {e}</span>")
                try:
                    with open(original_file, 'wb') as f:
                        f.write(response.content)
                    files.append(original_file)
                    print(f"<stroke style='color:yellow;'>[Info]:</stroke> Imagem salva diretamente: {original_file}")
                except Exception as save_error:
                    print(f"<stroke style='color:red;'>[Error]:</stroke> Falha ao salvar imagem: {save_error}")

            if fn != None:
                fn(math.ceil((i + 1) * 100 / total_pages))
            page_number += 1

        if fn != None:
            fn(100)

        return Chapter(pages.number, files)