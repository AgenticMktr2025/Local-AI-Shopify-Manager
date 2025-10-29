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

    async def _is_ollama_available(self) -> bool:
        """Check if the Ollama server is running and has models."""
        try:
            import ollama

            response = await asyncio.wait_for(ollama.aio.ps(), timeout=2)
            return (
                "models" in response
                and isinstance(response["models"], list)
                and response["models"]
            )
        except ImportError as e:
            logging.exception(
                f"Ollama python package not installed, falling back. Error: {e}"
            )
            return False
        except (asyncio.TimeoutError, ollama.ResponseError) as e:
            logging.exception(
                f"Ollama server not reachable, falling back to other models. Error: {e}"
            )
            return False
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred while checking for Ollama, falling back. Error: {e}"
            )
            return False

    async def get_best_model(self) -> OpenAIChat | Ollama | OpenRouter | None:
        """Selects the best available model based on priority and availability."""
        if await self._is_ollama_available():
            return Ollama(id="gemma2")
        if self.settings.openrouter_api_key:
            return OpenRouter(
                id="mistralai/mistral-7b-instruct",
                api_key=self.settings.openrouter_api_key,
            )
        if self.settings.openai_api_key:
            return OpenAIChat(id="gpt-3.5-turbo", api_key=self.settings.openai_api_key)
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
        tools = [DuckDuckGoTools()]
        if settings.are_shopify_credentials_set:
            tools.append(ShopifyTools())
        if model:
            self.current_model_name = model.id
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