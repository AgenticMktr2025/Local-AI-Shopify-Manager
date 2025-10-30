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
from agno.exceptions import ModelProviderError


class AIOrchestrator:
    """Manages AI model selection and fallback logic for cloud-based models."""

    def __init__(self, settings_state: "rx.State"):
        self.settings = settings_state
        self.client_cache: dict[str, OpenAIChat | OpenRouter] = {}
        self.current_model_name: str = ""

    async def get_best_model(self) -> MistralChat | OpenAIChat | OpenRouter | None:
        """Selects the best available model based on priority: OpenRouter -> Mistral -> OpenAI."""
        if self.settings.openrouter_api_key:
            self.current_model_name = "OpenRouter (Deepseek)"
            logging.info(f"Using model: {self.current_model_name}")
            return OpenRouter(
                id="deepseek/deepseek-chat",
                api_key=self.settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Shopify AI Manager",
                },
            )
        if self.settings.mistral_api_key:
            self.current_model_name = "Mistral (mistral-large-latest)"
            logging.info(f"Using model: {self.current_model_name}")
            return MistralChat(
                id="mistral-large-latest", api_key=self.settings.mistral_api_key
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
        You are an expert Shopify AI Assistant for the store manager. Your primary goal is to help the manager run their store efficiently by using the provided tools. You are acting on behalf of the manager, not interacting with end customers.

        **Your Role:**
        - You are the manager's personal assistant. When the user says "my", "I", or "me", they are referring to themselves as the store manager.
        - You must use the available tools to answer questions and perform actions related to the Shopify store's administration.

        **Tool Usage Guidelines:**
        - **Admin Tools (Default):** Use these for all internal management tasks. This includes looking up orders, products, customers, and performing actions like creating, updating, or deleting resources. For any query about store data (e.g., "show me the last order"), you should use an Admin tool.
        - **Storefront Tools (`[Storefront]`):** Only use these when the user explicitly asks to see something from a *customer's perspective* (e.g., "what does a customer see on the homepage?").
        - **DuckDuckGo:** Use for general knowledge questions that are not related to the Shopify store data.

        **Example Interaction:**
        User: "when was my last order placed and for how much was it for?"
        Assistant's Thought Process:
        1. The user is the store manager and is asking for the most recent order in the store.
        2. I need to find a tool to get order information.
        3. The `get_orders` tool seems appropriate. It can fetch recent orders.
        4. I will call `get_orders(limit=1)` to get the very last order.
        5. After getting the order details, I will present the date and price to the user.

        **Important:**
        - Never ask the user for their customer ID or email. You have direct access to the store's data through the tools.
        - If a tool fails, clearly state the error and suggest a possible reason if available.
        - Be concise and action-oriented in your responses.
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
            user_query = self.messages[-1]["content"]
            ambiguous_terms = [
                "my order",
                "my product",
                "my customer",
                "last order",
                "recent order",
                "my inventory",
                "my sales",
            ]
            if any((term in user_query.lower() for term in ambiguous_terms)):
                context_reminder = (
                    "[CONTEXT: User is store manager asking about store data] "
                )
                enhanced_query = context_reminder + user_query
            else:
                enhanced_query = user_query
            response_stream = self._agent.arun(
                enhanced_query, history=history, stream=True
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
        except ModelProviderError as e:
            logging.exception(f"Model provider error during agent execution: {e}")
            await self.on_load()
            self.messages.append(
                {
                    "role": "assistant",
                    "content": f"The current AI model failed. Trying a different model. Please ask your question again.",
                }
            )
        except Exception as e:
            logging.exception(f"Error during agent execution: {e}")
            self.messages.append(
                {"role": "assistant", "content": f"An unexpected error occurred: {e}"}
            )
        finally:
            self.is_processing = False