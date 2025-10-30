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
        self.client_cache: dict[str, OpenAIChat | OpenRouter | MistralChat] = {}
        self.current_model_name: str = ""

    async def get_fallback_models(
        self,
    ) -> list[tuple[MistralChat | OpenAIChat | OpenRouter, str]]:
        """Returns a prioritized list of available fallback models."""
        models = []
        if self.settings.openrouter_api_key:
            try:
                models.append(
                    (
                        OpenRouter(
                            id="mistralai/ministral-8b",
                            api_key=self.settings.openrouter_api_key,
                            base_url="https://openrouter.ai/api/v1",
                            default_headers={
                                "HTTP-Referer": "http://localhost:3000",
                                "X-Title": "Shopify AI Manager",
                            },
                        ),
                        "OpenRouter (Ministral 8B)",
                    )
                )
            except Exception as e:
                logging.exception(f"Could not initialize OpenRouter model: {e}")
        if self.settings.mistral_api_key:
            try:
                models.append(
                    (
                        MistralChat(
                            id="mistral-large-latest",
                            api_key=self.settings.mistral_api_key,
                        ),
                        "Mistral (mistral-large-latest)",
                    )
                )
            except Exception as e:
                logging.exception(f"Could not initialize Mistral model: {e}")
        if self.settings.openai_api_key:
            try:
                models.append(
                    (
                        OpenAIChat(
                            id="gpt-3.5-turbo", api_key=self.settings.openai_api_key
                        ),
                        "OpenAI (GPT-3.5 Turbo)",
                    )
                )
            except Exception as e:
                logging.exception(f"Could not initialize OpenAI model: {e}")
        return models


class ChatState(rx.State):
    """Manages the chat interface and AI agent interaction."""

    messages: list[dict[str, str]] = []
    is_processing: bool = False
    current_model_name: str = ""
    _agent: Agent | None = None

    @rx.event
    async def on_load(self) -> None:
        """Initializes the agent when the page loads."""
        await self._initialize_agent("")

    async def _initialize_agent(self, query: str):
        """Initializes or re-initializes the agent based on the query."""
        from app.states.settings_state import SettingsState
        from app.tools.shopify_tools import ShopifyTools
        from app.tools.shopify_storefront_tools import ShopifyStorefrontTools

        settings = await self.get_state(SettingsState)
        orchestrator = AIOrchestrator(settings)
        model = await orchestrator.get_best_model(query)
        self.current_model_name = orchestrator.current_model_name
        tools = [DuckDuckGoTools()]
        if settings.are_shopify_credentials_set:
            tools.append(ShopifyTools())
        if settings.is_shopify_storefront_token_set:
            tools.append(ShopifyStorefrontTools())
        system_prompt = """
        ⚠️ CRITICAL CONTEXT - READ FIRST ⚠️

        YOU ARE ASSISTING A STORE MANAGER/OWNER, NOT A CUSTOMER.

        The person you're talking to:
        - ✅ IS: A Shopify store owner/manager/administrator  
        - ❌ IS NOT: A customer shopping on the store
        - ✅ HAS: Full admin access to ALL store data (orders, customers, products, etc.)
        - ❌ SHOULD NOT: Ever be asked for customer ID, email, or personal identification

        When the user says "my orders", "my products", "my customers":
        - ✅ MEANS: The store's orders/products/customers (all of them)
        - ❌ DOES NOT MEAN: Their personal customer account

        ===== CORE INSTRUCTIONS =====

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

        ⚠️ REMEMBER: You are helping a STORE OWNER manage their BUSINESS, not a customer making a purchase. ⚠️
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
        self.is_processing = True
        self.messages.append({"role": "user", "content": question})
        yield
        from app.states.settings_state import SettingsState
        from app.tools.shopify_tools import ShopifyTools
        from app.tools.shopify_storefront_tools import ShopifyStorefrontTools

        settings = await self.get_state(SettingsState)
        orchestrator = AIOrchestrator(settings)
        fallback_models = await orchestrator.get_fallback_models()
        if not fallback_models:
            self.messages.append(
                {
                    "role": "assistant",
                    "content": "No AI models are available. Please configure API keys in settings.",
                }
            )
            self.is_processing = False
            return
        MAX_RETRIES = 3
        for i, (model, model_name) in enumerate(fallback_models):
            if i >= MAX_RETRIES:
                break
            try:
                self.current_model_name = model_name
                logging.info(f"Attempt {i + 1}/{MAX_RETRIES}: Using model {model_name}")
                tools = [DuckDuckGoTools()]
                if settings.are_shopify_credentials_set:
                    tools.append(ShopifyTools())
                if settings.is_shopify_storefront_token_set:
                    tools.append(ShopifyStorefrontTools())
                system_prompt = "..."
                agent = Agent(
                    model=model,
                    tools=tools,
                    markdown=True,
                    system_message=system_prompt,
                )
                history = [Message(**msg) for msg in self.messages[:-1]]
                user_query = self.messages[-1]["content"]
                response_stream = agent.arun(user_query, history=history, stream=True)
                assistant_message_initialized = False
                full_response = ""
                async for event in cast(AsyncGenerator, response_stream):
                    if hasattr(event, "content") and event.content:
                        if not assistant_message_initialized:
                            self.messages.append({"role": "assistant", "content": ""})
                            assistant_message_initialized = True
                        chunk = event.content
                        if isinstance(chunk, str):
                            full_response += chunk
                            self.messages[-1]["content"] = full_response
                            yield
                self.is_processing = False
                return
            except ModelProviderError as e:
                logging.exception(
                    f"Model provider error with {model_name} on attempt {i + 1}: {e}"
                )
                if self.messages and self.messages[-1]["role"] == "assistant":
                    self.messages.pop()
                if i < len(fallback_models) - 1 and i < MAX_RETRIES - 1:
                    yield rx.toast(
                        f"Model {model_name.split('(')[0].strip()} failed, trying next...",
                        duration=3000,
                    )
                    continue
                else:
                    self.messages.append(
                        {
                            "role": "assistant",
                            "content": f"All AI models failed to respond. Please check your API keys or try again later. Error: {e}",
                        }
                    )
                    break
            except Exception as e:
                logging.exception(
                    f"An unexpected error occurred with {model_name}: {e}"
                )
                if self.messages and self.messages[-1]["role"] == "assistant":
                    self.messages.pop()
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": f"An unexpected error occurred: {e}",
                    }
                )
                break
        self.is_processing = False