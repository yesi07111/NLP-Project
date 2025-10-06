import os
import json
import re
from datetime import datetime

def ensure_cache_directory():
    """Crear directorio de caché si no existe"""
    cache_dir = "_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_chat_cache_filename(chat_info):
    """Obtener nombre de archivo de caché para un chat"""
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", chat_info["name"])
    chat_id = chat_info.get("id", "unknown")
    return f"{safe_name}_{chat_id}_preview.json"


def save_chat_to_cache(chat_info, messages):
    """Guardar mensajes en caché"""
    try:
        cache_dir = ensure_cache_directory()
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", chat_info.get("name", "chat"))
        chat_id = chat_info.get("id", "unknown")
        cache_file = os.path.join(cache_dir, f"{safe_name}_{chat_id}_preview.json")

        safe_chat = {
            "id": chat_info.get("id"),
            "name": chat_info.get("name"),
            "unread_count": chat_info.get("unread_count", 0),
        }
        ent = chat_info.get("entity")
        if ent is not None:
            try:
                safe_chat["entity_id"] = getattr(ent, "id", None)
                safe_chat["entity_type"] = type(ent).__name__
                safe_chat["username"] = getattr(ent, "username", None)
                safe_chat["title"] = getattr(ent, "title", None)
            except Exception:
                pass

        cache_data = {
            "chat_info": safe_chat,
            "messages": messages,
            "cached_at": datetime.now().isoformat(),
            "message_count": len(messages),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"Chat guardado en caché: {cache_file}")
        return True
    except Exception as e:
        print(f"Error guardando en caché: {e}")
        return False


def load_chat_from_cache(chat_info, max_age_hours=24):
    """Cargar mensajes desde caché si no son muy viejos"""
    try:
        cache_dir = ensure_cache_directory()
        cache_file = os.path.join(cache_dir, get_chat_cache_filename(chat_info))

        if not os.path.exists(cache_file):
            return None

        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if (datetime.now() - file_time).total_seconds() > max_age_hours * 3600:
            print("Caché muy antiguo, ignorando...")
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        print(f"Cargado desde caché: {len(cache_data['messages'])} mensajes")
        return cache_data["messages"]
    except Exception as e:
        print(f"Error cargando desde caché: {e}")
        return None


def save_session_info(phone, password=None):
    """Guardar info mínima de sesión en _cache/session_info.json"""
    try:
        cache_dir = ensure_cache_directory()
        session_file = os.path.join(cache_dir, "session_info.json")
        data = {"phone": phone or "", "password": password or ""}
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando session_info: {e}")


def load_session_info():
    """Leer session_info.json si existe"""
    try:
        cache_dir = ensure_cache_directory()
        session_file = os.path.join(cache_dir, "session_info.json")
        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error leyendo session_info: {e}")
    return None

