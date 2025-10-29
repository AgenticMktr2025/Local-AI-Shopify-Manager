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
    openai_test_result: AITestResult | None = None
    openrouter_test_result: AITestResult | None = None

    async def _test_openai(self, api_key: str):
        if not api_key:
            self.openai_test_result = {
                "success": False,
                "model": "openai",
                "error": "API key is not set.",
            }
            return
        try:
            client = openai.AsyncOpenAI(api_key=api_key)
            await client.models.list()
            self.openai_test_result = {
                "success": True,
                "model": "openai",
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
                base_url="https://openrouter.ai/api/v1", api_key=api_key
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

    @rx.event
    async def test_api_key(self, model: Literal["openai", "openrouter"]):
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