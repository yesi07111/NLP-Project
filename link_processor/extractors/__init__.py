from .base import get_extractor, register_extractor, BaseExtractor

# Importar todos los extractores para que se registren automáticamente
from . import instagram
from . import youtube
from . import twitter
from . import github
from . import reddit
from . import facebook
from . import linkedin
from . import threads
from . import whatsapp
from . import discord
from . import flickr
from . import likee
from . import medium
from . import pinterest
from . import snapchat
from . import stackoverflow
from . import tumblr
from . import amazon
from . import gitlab
from . import google
from . import imgur
from . import telegram
# ... importar nuevos extractores aquí

__all__ = ['get_extractor', 'register_extractor', 'BaseExtractor']