import re
import os
import markdown
from bs4 import BeautifulSoup
from link_processor.main import LinkProcessor

os.makedirs('chats', exist_ok=True)

def clean_message_text(text: str) -> str:
    """Limpia el texto de un mensaje reemplazando enlaces por descripciones detalladas"""

    def strip_markdown(text: str) -> str:
        html = markdown.markdown(text, extensions=["extra", "sane_lists"])
        soup = BeautifulSoup(html, "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        return cleaned

    link_processor = LinkProcessor()
    url_pattern = re.compile(r'https?://[^\s]+')
    cleaned = re.sub(url_pattern, link_processor.replace_link, text)
    raw = strip_markdown(cleaned)

    return raw.strip()

def sanitize_filename(filename):
    """Limpiar nombre de archivo"""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)