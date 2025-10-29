import reflex as rx
import os
from dotenv import load_dotenv

load_dotenv()


class SettingsState(rx.State):
    """Manages app settings, including API keys and Shopify credentials."""

    shopify_store_url: str = os.getenv("SHOPIFY_STORE_URL") or ""
    shopify_access_token: str = os.getenv("SHOPIFY_ACCESS_TOKEN") or ""
    openai_api_key: str = os.getenv("OPENAI_API_KEY") or ""
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY") or ""
    show_shopify_token: bool = False
    show_openai_key: bool = False
    show_openrouter_key: bool = False

    @rx.var
    def are_shopify_credentials_set(self) -> bool:
        """Check if both Shopify store URL and access token are configured."""
        return bool(self.shopify_store_url and self.shopify_access_token)

    @rx.var
    def is_openai_key_set(self) -> bool:
        """Check if OpenAI API key is set."""
        return bool(self.openai_api_key)

    @rx.var
    def is_openrouter_key_set(self) -> bool:
        """Check if OpenRouter API key is set."""
        return bool(self.openrouter_api_key)

    @rx.event
    def toggle_visibility(self, key: str):
        if key == "shopify":
            self.show_shopify_token = not self.show_shopify_token
        elif key == "openai":
            self.show_openai_key = not self.show_openai_key
        elif key == "openrouter":
            self.show_openrouter_key = not self.show_openrouter_key