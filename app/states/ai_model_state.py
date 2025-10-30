import reflex as rx
import logging
from typing import TypedDict, Literal
import openai


class AITestResult(TypedDict):
    success: bool
    model: str
    error: str | None


class AIModelState(rx.State):
    """Manages AI model API key testing."""

    is_testing_openai: bool = False
    is_testing_openrouter: bool = False
    is_testing_mistral: bool = False
    is_testing_shopify_storefront: bool = False
    openai_test_result: AITestResult | None = None
    openrouter_test_result: AITestResult | None = None
    mistral_test_result: AITestResult | None = None
    shopify_storefront_test_result: AITestResult | None = None

    async def _test_openai(self, api_key: str):
        if not api_key:
            self.openai_test_result = {
                "success": False,
                "model": "openai",
                "error": "API key is not set.",
            }
        try:
            client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Shopify AI Manager",
                },
            )
            await client.models.list()
            self.openrouter_test_result = {
                "success": True,
                "model": "openrouter",
                "error": None,
            }
        except Exception as e:
            logging.exception(f"OpenAI API key test failed: {e}")
            self.openai_test_result = {
                "success": False,
                "model": "openai",
                "error": str(e),
            }

    async def _test_openrouter(self, api_key: str):
        if not api_key:
            self.openrouter_test_result = {
                "success": False,
                "model": "openrouter",
                "error": "API key is not set.",
            }
            return
        try:
            client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Shopify AI Manager",
                },
            )
            await client.models.list()
            self.openrouter_test_result = {
                "success": True,
                "model": "openrouter",
                "error": None,
            }
        except Exception as e:
            logging.exception(f"OpenRouter API key test failed: {e}")
            self.openrouter_test_result = {
                "success": False,
                "model": "openrouter",
                "error": str(e),
            }

    async def _test_mistral(self, api_key: str):
        if not api_key:
            self.mistral_test_result = {
                "success": False,
                "model": "mistral",
                "error": "API key is not set.",
            }
            return
        try:
            client = openai.AsyncOpenAI(
                base_url="https://api.mistral.ai/v1", api_key=api_key
            )
            await client.models.list()
            self.mistral_test_result = {
                "success": True,
                "model": "mistral",
                "error": None,
            }
        except Exception as e:
            logging.exception(f"Mistral API key test failed: {e}")
            self.mistral_test_result = {
                "success": False,
                "model": "mistral",
                "error": str(e),
            }

    async def _test_shopify_storefront(self, api_key: str, store_url: str):
        if not api_key or not store_url:
            self.shopify_storefront_test_result = {
                "success": False,
                "model": "shopify_storefront",
                "error": "API key or store URL is not set.",
            }
            return
        try:
            import httpx

            endpoint = f"https://{store_url}/api/2024-04/graphql.json"
            headers = {
                "X-Shopify-Storefront-Access-Token": api_key,
                "Content-Type": "application/json",
            }
            query = {"query": "{ shop { name } }"}
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=query, headers=headers)
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    raise Exception(data["errors"])
            self.shopify_storefront_test_result = {
                "success": True,
                "model": "shopify_storefront",
                "error": None,
            }
        except Exception as e:
            logging.exception(f"Shopify Storefront API key test failed: {e}")
            self.shopify_storefront_test_result = {
                "success": False,
                "model": "shopify_storefront",
                "error": str(e),
            }

    @rx.event
    async def test_api_key(
        self, model: Literal["openai", "openrouter", "mistral", "shopify_storefront"]
    ):
        """Tests the API key for the specified model."""
        from app.states.settings_state import SettingsState

        settings = await self.get_state(SettingsState)
        if model == "openai":
            self.is_testing_openai = True
            self.openai_test_result = None
            yield
            await self._test_openai(settings.openai_api_key)
            self.is_testing_openai = False
        elif model == "openrouter":
            self.is_testing_openrouter = True
            self.openrouter_test_result = None
            yield
            await self._test_openrouter(settings.openrouter_api_key)
            self.is_testing_openrouter = False
        elif model == "mistral":
            self.is_testing_mistral = True
            self.mistral_test_result = None
            yield
            await self._test_mistral(settings.mistral_api_key)
            self.is_testing_mistral = False
        elif model == "shopify_storefront":
            self.is_testing_shopify_storefront = True
            self.shopify_storefront_test_result = None
            yield
            await self._test_shopify_storefront(
                settings.shopify_storefront_token, settings.shopify_store_url
            )
            self.is_testing_shopify_storefront = False