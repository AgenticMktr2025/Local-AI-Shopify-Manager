import reflex as rx
import os
import asyncio
import logging
from typing import AsyncGenerator, cast
from agno.agent import Agent, Message
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter
from agno.models.mistral import MistralChat


class AIOrchestrator:
    """Manages AI model selection and fallback logic for cloud-based models."""

    def __init__(self, settings_state: "rx.State"):
        self.settings = settings_state
        self.client_cache: dict[str, OpenAIChat | OpenRouter] = {}
        self.current_model_name: str = ""

    async def get_best_model(self) -> MistralChat | OpenAIChat | OpenRouter | None:
        """Selects the best available model based on priority: Mistral -> OpenRouter -> OpenAI."""
        if self.settings.is_mistral_key_set:
            self.current_model_name = "Mistral (mistral-large-latest)"
            logging.info(f"Using model: {self.current_model_name}")
            return MistralChat(
                id="mistral-large-latest", api_key=self.settings.mistral_api_key
            )
        if self.settings.is_openrouter_key_set:
            self.current_model_name = "OpenRouter (Mistral)"
            logging.info(f"Using model: {self.current_model_name}")
            return OpenRouter(
                id="mistralai/mistral-7b-instruct",
                api_key=self.settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        if self.settings.is_openai_key_set:
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
        from app.tools.shopify_storefront_tools import ShopifyStorefrontTools

        settings = await self.get_state(SettingsState)
        orchestrator = AIOrchestrator(settings)
        model = await orchestrator.get_best_model()
        self.current_model_name = orchestrator.current_model_name
        tools = [DuckDuckGoTools()]
        if settings.are_shopify_credentials_set:
            tools.append(ShopifyTools())
        if settings.is_shopify_storefront_token_set:
            tools.append(ShopifyStorefrontTools())
        system_prompt = """
        You are a Shopify AI Assistant. Your goal is to help users manage their Shopify store by using the provided tools. 

        - You have two sets of Shopify tools: Admin tools (default) and Storefront tools (prefixed with `[Storefront]` in the description).
        - Use Admin tools for management tasks like creating products, updating orders, or viewing internal data.
        - Use Storefront tools for public-facing queries, like checking what a customer sees in the online store.
        - For general knowledge questions, use the DuckDuckGo search tool.
        - When a user asks to perform an action (e.g., 'create a product'), use the corresponding tool and confirm the successful completion of the action.
        - If a tool fails, inform the user about the error and ask for clarification if needed.
        - Be concise and clear in your responses.
        """
        if model:
            self._agent = Agent(
                model=model, tools=tools, markdown=True, system_message=system_prompt
            )
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