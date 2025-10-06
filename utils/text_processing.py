import re
from urllib.parse import urlparse
import markdown
from bs4 import BeautifulSoup

def clean_message_text(text: str) -> str:
    """Limpia el texto de un mensaje reemplazando enlaces por descripciones"""
    
    def replace_link(match):
        url = match.group(0)
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "instagram.com" in domain:
            if "/reel/" in parsed.path:
                return "[Reel de Instagram]"
            elif "/stories/" in parsed.path:
                return "[Historia de Instagram]"
            elif "/p/" in parsed.path:
                return "[Publicación de Instagram]"
            else:
                return "[Perfil o contenido de Instagram]"

        elif "youtube.com" in domain or "youtu.be" in domain:
            if "shorts" in parsed.path:
                return "[YouTube Short]"
            elif "watch" in parsed.path or "youtu.be" in domain:
                return "[Video de YouTube]"
            else:
                return "[Canal o enlace de YouTube]"

        elif "tiktok.com" in domain:
            if "/video/" in parsed.path:
                return "[Video de TikTok]"
            elif "/@" in parsed.path:
                return "[Perfil de TikTok]"
            else:
                return "[Contenido de TikTok]"

        elif "twitter.com" in domain or "x.com" in domain:
            if "/status/" in parsed.path:
                return "[Tweet de X/Twitter]"
            elif "/@" in parsed.path:
                return "[Perfil de X/Twitter]"
            else:
                return "[Contenido de X/Twitter]"

        elif "facebook.com" in domain:
            if "/reel/" in parsed.path:
                return "[Reel de Facebook]"
            elif "/posts/" in parsed.path:
                return "[Publicación de Facebook]"
            elif "/story.php" in parsed.path:
                return "[Historia de Facebook]"
            else:
                return "[Contenido de Facebook]"

        elif "reddit.com" in domain:
            if "/r/" in parsed.path:
                return "[Publicación o hilo en Reddit]"
            else:
                return "[Contenido de Reddit]"

        elif "t.me" in domain or "telegram.me" in domain:
            if "/joinchat" in parsed.path or "/+" in parsed.path:
                return "[Invitación a grupo de Telegram]"
            elif "/@" in parsed.path or parsed.path.strip("/"):
                return "[Canal o usuario de Telegram]"
            else:
                return "[Enlace de Telegram]"

        elif "threads.net" in domain:
            return "[Publicación de Threads]"

        domain_name = re.sub(r"^www\.", "", domain)
        base_name = domain_name.split(".")[0].capitalize()
        return f"[Enlace a {base_name}]"

    def strip_markdown(text: str) -> str:
        html = markdown.markdown(text, extensions=["extra", "sane_lists"])
        soup = BeautifulSoup(html, "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        return cleaned

    url_pattern = re.compile(r"https?://[^\s]+")
    cleaned = re.sub(url_pattern, replace_link, text)
    raw = strip_markdown(cleaned)

    return raw.strip()


def sanitize_filename(filename):
    """Limpiar nombre de archivo"""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)

