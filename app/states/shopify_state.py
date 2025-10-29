import reflex as rx
import shopify
import logging
from typing import TypedDict


class TestResult(TypedDict):
    success: bool
    shop_name: str | None
    error: str | None


class ShopifyState(rx.State):
    """Manages Shopify API connection and data fetching."""

    is_testing: bool = False
    test_result: TestResult | None = None

    @rx.event
    async def test_connection(self):
        """Tests the Shopify API connection using credentials from SettingsState."""
        from app.states.settings_state import SettingsState

        self.is_testing = True
        self.test_result = None
        yield
        settings = await self.get_state(SettingsState)
        if not settings.are_shopify_credentials_set:
            self.test_result = {
                "success": False,
                "shop_name": None,
                "error": "Shopify credentials are not set.",
            }
            self.is_testing = False
            return
        try:
            session = shopify.Session(
                settings.shopify_store_url, "2024-04", settings.shopify_access_token
            )
            shopify.ShopifyResource.activate_session(session)
            query = """
            {
              shop {
                name
              }
            }
            """
            result = shopify.GraphQL().execute(query)
            shop_data = result.get("data", {}).get("shop", {})
            shop_name = shop_data.get("name")
            if shop_name:
                self.test_result = {
                    "success": True,
                    "shop_name": shop_name,
                    "error": None,
                }
            else:
                error_message = result.get("errors", "Unknown error")
                self.test_result = {
                    "success": False,
                    "shop_name": None,
                    "error": str(error_message),
                }
        except Exception as e:
            logging.exception(f"Shopify connection test failed: {e}")
            self.test_result = {"success": False, "shop_name": None, "error": str(e)}
        finally:
            shopify.ShopifyResource.clear_session()
            self.is_testing = False