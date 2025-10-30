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

    async def get_best_model(
        self, query: str = ""
    ) -> MistralChat | OpenAIChat | OpenRouter | None:
        """Selects the best available model based on priority and query type."""
        deep_research_keywords = ["research", "deep dive", "analyze", "report on"]
        is_research_query = any(
            (keyword in query.lower() for keyword in deep_research_keywords)
        )
        if self.settings.openrouter_api_key:
            try:
                model_id = "deepseek/deepseek-chat"
                self.current_model_name = "OpenRouter (DeepSeek Chat)"
                if is_research_query:
                    model_id = "alibaba/tongyi-deepresearch-30b-a3b:free"
                    self.current_model_name = "OpenRouter (Tongyi DeepResearch)"
                logging.info(f"Using model: {self.current_model_name}")
                return OpenRouter(
                    id=model_id,
                    api_key=self.settings.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Shopify AI Manager",
                    },
                )
            except Exception as e:
                logging.exception(
                    f"Failed to initialize primary OpenRouter model, falling back. Error: {e}"
                )
                self.current_model_name = "OpenRouter (GPT-4o Mini)"
                logging.info(f"Using model: {self.current_model_name}")
                return OpenRouter(
                    id="openai/gpt-4o-mini",
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
        yield
        await self._initialize_agent(question)
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
                "my store",
            ]
            if any((term in user_query.lower() for term in ambiguous_terms)):
                enhanced_query = f"[STORE MANAGER QUERY - Store Data Only] {user_query}"
            else:
                enhanced_query = user_query
            response_stream = self._agent.arun(
                enhanced_query, history=history, stream=True
            )
            assistant_message_initialized = False
            full_response = ""
            async for event in cast(AsyncGenerator, response_stream):
                if hasattr(event, "content") and event.content:
                    if not assistant_message_initialized:
                        self.messages.append({"role": "assistant", "content": ""})
                        assistant_message_initialized = True
                        yield
                    chunk = event.content
                    if isinstance(chunk, str):
                        full_response += chunk
                        self.messages[-1]["content"] = full_response
                        yield
        except ModelProviderError as e:
            logging.exception(f"Model provider error during agent execution: {e}")
            if assistant_message_initialized:
                self.messages.pop()
            await self._initialize_agent(question)
            self.messages.append(
                {
                    "role": "assistant",
                    "content": f"The current AI model failed. Trying a different model. Please ask your question again.",
                }
            )
        except Exception as e:
            logging.exception(f"Error during agent execution: {e}")
            if assistant_message_initialized:
                self.messages.pop()
            self.messages.append(
                {"role": "assistant", "content": f"An unexpected error occurred: {e}"}
            )
        finally:
            self.is_processing = False