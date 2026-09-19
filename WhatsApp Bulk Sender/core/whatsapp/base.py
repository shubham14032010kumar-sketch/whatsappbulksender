"""
WhatsApp Provider Abstraction Base (core/whatsapp/base.py)
Allows seamless plug-and-play between Desktop Selenium automation
and Official Meta WhatsApp Business Cloud API.
"""

from abc import ABC, abstractmethod


class WhatsAppBaseProvider(ABC):
    """Abstract Base Class for WhatsApp dispatches."""

    @abstractmethod
    def initialize(self):
        """Initializes connection / session."""
        pass

    @abstractmethod
    def send_message(self, phone, text_content, media_path=None, sim_typing=True):
        """Dispatches a single message to phone. Returns (success: bool, status_msg: str)."""
        pass

    @abstractmethod
    def close(self):
        """Cleans up resources."""
        pass
