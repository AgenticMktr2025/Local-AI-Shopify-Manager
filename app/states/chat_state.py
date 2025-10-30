import reflex as rx
import os
import asyncio
import logging
from typing import AsyncGenerator, cast
from agno.agent import Agent, Message
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from agno.models.openrouter import OpenRouter


class AIOrchestrator:
    """Manages AI model selection and fallback logic."""

    def __init__(self, settings_state: "rx.State"):
        self.settings = settings_state
        self.client_cache: dict[str, OpenAIChat | Ollama | OpenRouter] = {}
        self.current_model_name: str = ""

    async def _is_ollama_available(self) -> bool:
        """Check if the Ollama server is running and has models. Fails silently."""
        try:
            import ollama

            response = await asyncio.wait_for(asyncio.to_thread(ollama.list), timeout=2)
            return bool(response.get("models"))
        except Exception as e:
            logging.exception(f"Ollama check failed: {e}")
            return False

    async def get_best_model(self) -> OpenAIChat | Ollama | OpenRouter | None:
        """Selects the best available model based on priority and availability."""
        if await self._is_ollama_available():
            self.current_model_name = "Native AI (phi3:mini)"
            logging.info(f"Using model: {self.current_model_name}")
            return Ollama(id="phi3:mini")
        if self.settings.openrouter_api_key:
            self.current_model_name = "OpenRouter (Mistral)"
            logging.info(f"Using model: {self.current_model_name}")
            return OpenRouter(
                id="mistralai/mistral-7b-instruct",
                api_key=self.settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        if self.settings.openai_api_key:
            self.current_model_name = "OpenAI (GPT-3.5 Turbo)"
            logging.info(f"Using model: {self.current_model_name}")
            return OpenAIChat(id="gpt-3.5-turbo", api_key=self.settings.openai_api_key)
        self.current_model_name = "No model available"
        logging.warning(
            "No AI models are available. Please configure API keys in settings."
        )
        return None


class ChatState(rx.State):
    """Manages the chat interface and AI agent interaction."""

    messages: list[dict[str, str]] = []
    is_processing: bool = False
    current_model_name: str = ""
    _agent: Agent | None = None

    @rx.event
    async def on_load(self) -> None:
        """Initializes the agent when the page loads."""
        from app.states.settings_state import SettingsState
        from app.tools.shopify_tools import ShopifyTools

        settings = await self.get_state(SettingsState)
        orchestrator = AIOrchestrator(settings)
        model = await orchestrator.get_best_model()
        self.current_model_name = orchestrator.current_model_name
        tools = [DuckDuckGoTools()]
        if settings.are_shopify_credentials_set:
            tools.append(ShopifyTools())
        if model:
            self._agent = Agent(model=model, tools=tools, markdown=True)
        else:
            self.current_model_name = "No model available"

    @rx.event
    async def answer(self, form_data: dict[str, str]):
        """Processes the user's question and streams the agent's response."""
        question = form_data.get("question", "").strip()
        if not question or self.is_processing:
            return
        yield
        if not self._agent:
            await self.on_load()
            if not self._agent:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": "No AI models are available. Please configure API keys in settings.",
                    }
                )
                return
        self.is_processing = True
        self.messages.append({"role": "user", "content": question})
        yield
        try:
            history = [Message(**msg) for msg in self.messages[:-1]]
            response_stream = self._agent.arun(
                self.messages[-1]["content"], history=history, stream=True
            )
            self.messages.append({"role": "assistant", "content": ""})
            yield
            full_response = ""
            async for event in cast(AsyncGenerator, response_stream):
                if hasattr(event, "content") and event.content:
                    chunk = event.content
                    if isinstance(chunk, str):
                        full_response += chunk
                        self.messages[-1]["content"] = full_response
                        yield
        except Exception as e:
            logging.exception(f"Error during agent execution: {e}")
            self.messages.append(
                {"role": "assistant", "content": f"An error occurred: {e}"}
            )
        finally:
            self.is_processing = False