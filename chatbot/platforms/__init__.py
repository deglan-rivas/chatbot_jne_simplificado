# Platforms module
from chatbot.platforms.base import PlatformAdapter
from chatbot.platforms.web_adapter import WebAdapter

__all__ = ["PlatformAdapter", "WebAdapter"]
