import reflex as rx


class SettingsState(rx.State):
    """Manages app settings, including API keys and Shopify credentials."""

    shopify_store_url: str = ""
    shopify_access_token: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    show_shopify_token: bool = False
    show_openai_key: bool = False
    show_openrouter_key: bool = False

    @rx.var
    def are_shopify_credentials_set(self) -> bool:
        """Check if both Shopify store URL and access token are configured."""
        return bool(self.shopify_store_url and self.shopify_access_token)

    @rx.event
    def toggle_visibility(self, key: str):
        if key == "shopify":
            self.show_shopify_token = not self.show_shopify_token
        elif key == "openai":
            self.show_openai_key = not self.show_openai_key
        elif key == "openrouter":
            self.show_openrouter_key = not self.show_openrouter_key