import reflex as rx
from app.states.settings_state import SettingsState
from app.states.shopify_state import ShopifyState
from app.states.ai_model_state import AIModelState
from app.components.sidebar import page_layout


def api_key_input(
    label: str,
    name: str,
    value: rx.Var[str],
    on_change: rx.event.EventHandler,
    is_visible: rx.Var[bool],
    toggle_visibility: rx.event.EventHandler,
) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="text-sm font-medium text-gray-700"),
        rx.el.div(
            rx.el.input(
                type=rx.cond(is_visible, "text", "password"),
                name=name,
                default_value=value,
                on_change=on_change,
                class_name="flex-1 p-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white",
            ),
            rx.el.button(
                rx.icon(rx.cond(is_visible, "eye-off", "eye"), size=18),
                on_click=toggle_visibility,
                class_name="p-2 border-t border-b border-r rounded-r-md hover:bg-gray-100",
            ),
            class_name="flex items-center mt-1",
        ),
    )


def settings_page() -> rx.Component:
    content = rx.el.div(
        rx.el.h1("Settings", class_name="text-2xl font-bold mb-6"),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Shopify Credentials", class_name="text-lg font-semibold mb-4"
                ),
                rx.el.div(
                    rx.el.label(
                        "Shopify Store URL",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        placeholder="your-store.myshopify.com",
                        name="shopify_store_url",
                        default_value=SettingsState.shopify_store_url,
                        on_change=SettingsState.set_shopify_store_url,
                        class_name="w-full p-2 border rounded-md mt-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500",
                    ),
                    class_name="space-y-2 mb-4",
                ),
                api_key_input(
                    "Shopify Admin Access Token",
                    "shopify_access_token",
                    SettingsState.shopify_access_token,
                    SettingsState.set_shopify_access_token,
                    SettingsState.show_shopify_token,
                    lambda: SettingsState.toggle_visibility("shopify"),
                ),
                rx.cond(
                    SettingsState.are_shopify_credentials_set,
                    rx.el.div(
                        rx.icon("check_check", size=16, class_name="text-green-500"),
                        rx.el.p(
                            "Shopify credentials are set.",
                            class_name="text-sm text-green-600",
                        ),
                        class_name="flex items-center gap-2 mt-2",
                    ),
                    rx.el.div(
                        rx.icon(
                            "flag_triangle_right", size=16, class_name="text-yellow-500"
                        ),
                        rx.el.p(
                            "Shopify credentials are not set.",
                            class_name="text-sm text-yellow-600",
                        ),
                        class_name="flex items-center gap-2 mt-2",
                    ),
                ),
                rx.el.button(
                    "Test Shopify Connection",
                    on_click=ShopifyState.test_connection,
                    class_name="mt-4 w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400",
                    disabled=~SettingsState.are_shopify_credentials_set
                    | ShopifyState.is_testing,
                ),
                rx.cond(
                    ShopifyState.is_testing,
                    rx.el.div(
                        rx.spinner(class_name="h-4 w-4 text-gray-500"),
                        rx.el.p("Testing...", class_name="text-sm text-gray-500"),
                        class_name="flex items-center gap-2 mt-2",
                    ),
                    None,
                ),
                rx.cond(
                    ShopifyState.test_result,
                    rx.cond(
                        ShopifyState.test_result["success"],
                        rx.el.div(
                            rx.icon(
                                "check_check", size=16, class_name="text-green-500"
                            ),
                            rx.el.p(
                                f"Success! Connected to {ShopifyState.test_result['shop_name']}.",
                                class_name="text-sm text-green-600",
                            ),
                            class_name="flex items-center gap-2 mt-2",
                        ),
                        rx.el.div(
                            rx.icon("circle_x", size=16, class_name="text-red-500"),
                            rx.el.p(
                                f"Failed: {ShopifyState.test_result['error']}",
                                class_name="text-sm text-red-600",
                            ),
                            class_name="flex items-center gap-2 mt-2",
                        ),
                    ),
                    None,
                ),
                class_name="p-6 bg-white rounded-lg border",
            ),
            rx.el.div(
                rx.el.h2(
                    "Shopify Storefront API", class_name="text-lg font-semibold mb-4"
                ),
                api_key_input(
                    "Shopify Storefront Access Token",
                    "shopify_storefront_token",
                    SettingsState.shopify_storefront_token,
                    SettingsState.set_shopify_storefront_token,
                    SettingsState.show_shopify_storefront_token,
                    lambda: SettingsState.toggle_visibility("shopify_storefront"),
                ),
                rx.el.button(
                    "Test Storefront Token",
                    on_click=lambda: AIModelState.test_api_key("shopify_storefront"),
                    class_name="mt-4 w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400",
                    disabled=~SettingsState.is_shopify_storefront_token_set
                    | AIModelState.is_testing_shopify_storefront,
                ),
                rx.cond(
                    AIModelState.is_testing_shopify_storefront,
                    rx.el.div(
                        rx.spinner(class_name="h-4 w-4 text-gray-500"),
                        rx.el.p("Testing...", class_name="text-sm text-gray-500"),
                        class_name="flex items-center gap-2 mt-2",
                    ),
                    None,
                ),
                rx.cond(
                    AIModelState.shopify_storefront_test_result,
                    rx.cond(
                        AIModelState.shopify_storefront_test_result["success"],
                        rx.el.div(
                            rx.icon(
                                "check_check", size=16, class_name="text-green-500"
                            ),
                            rx.el.p(
                                "Success! Storefront token is valid.",
                                class_name="text-sm text-green-600",
                            ),
                            class_name="flex items-center gap-2 mt-2",
                        ),
                        rx.el.div(
                            rx.icon("circle_x", size=16, class_name="text-red-500"),
                            rx.el.p(
                                f"Failed: {AIModelState.shopify_storefront_test_result['error']}",
                                class_name="text-sm text-red-600",
                            ),
                            class_name="flex items-center gap-2 mt-2",
                        ),
                    ),
                    None,
                ),
                class_name="p-6 bg-white rounded-lg border",
            ),
            rx.el.div(
                rx.el.h2("AI Model API Keys", class_name="text-lg font-semibold mb-4"),
                rx.el.div(
                    rx.el.div(
                        api_key_input(
                            "OpenAI API Key",
                            "openai_api_key",
                            SettingsState.openai_api_key,
                            SettingsState.set_openai_api_key,
                            SettingsState.show_openai_key,
                            lambda: SettingsState.toggle_visibility("openai"),
                        ),
                        rx.el.button(
                            "Test Key",
                            on_click=lambda: AIModelState.test_api_key("openai"),
                            class_name="mt-2 w-full bg-gray-200 text-gray-700 p-2 rounded-md hover:bg-gray-300 disabled:bg-gray-100",
                            disabled=~SettingsState.is_openai_key_set
                            | AIModelState.is_testing_openai,
                        ),
                        rx.cond(
                            AIModelState.is_testing_openai,
                            rx.el.div(
                                rx.spinner(class_name="h-4 w-4 text-gray-500"),
                                rx.el.p(
                                    "Testing...", class_name="text-sm text-gray-500"
                                ),
                                class_name="flex items-center gap-2 mt-2",
                            ),
                            None,
                        ),
                        rx.cond(
                            AIModelState.openai_test_result,
                            rx.cond(
                                AIModelState.openai_test_result["success"],
                                rx.el.div(
                                    rx.icon(
                                        "check_check",
                                        size=16,
                                        class_name="text-green-500",
                                    ),
                                    rx.el.p(
                                        "Success! Key is valid.",
                                        class_name="text-sm text-green-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                                rx.el.div(
                                    rx.icon(
                                        "circle_x", size=16, class_name="text-red-500"
                                    ),
                                    rx.el.p(
                                        f"Failed: {AIModelState.openai_test_result['error']}",
                                        class_name="text-sm text-red-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                            ),
                            None,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        api_key_input(
                            "OpenRouter API Key",
                            "openrouter_api_key",
                            SettingsState.openrouter_api_key,
                            SettingsState.set_openrouter_api_key,
                            SettingsState.show_openrouter_key,
                            lambda: SettingsState.toggle_visibility("openrouter"),
                        ),
                        rx.el.button(
                            "Test Key",
                            on_click=lambda: AIModelState.test_api_key("openrouter"),
                            class_name="mt-2 w-full bg-gray-200 text-gray-700 p-2 rounded-md hover:bg-gray-300 disabled:bg-gray-100",
                            disabled=~SettingsState.is_openrouter_key_set
                            | AIModelState.is_testing_openrouter,
                        ),
                        rx.cond(
                            AIModelState.is_testing_openrouter,
                            rx.el.div(
                                rx.spinner(class_name="h-4 w-4 text-gray-500"),
                                rx.el.p(
                                    "Testing...", class_name="text-sm text-gray-500"
                                ),
                                class_name="flex items-center gap-2 mt-2",
                            ),
                            None,
                        ),
                        rx.cond(
                            AIModelState.openrouter_test_result,
                            rx.cond(
                                AIModelState.openrouter_test_result["success"],
                                rx.el.div(
                                    rx.icon(
                                        "check_check",
                                        size=16,
                                        class_name="text-green-500",
                                    ),
                                    rx.el.p(
                                        "Success! Key is valid.",
                                        class_name="text-sm text-green-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                                rx.el.div(
                                    rx.icon(
                                        "circle_x", size=16, class_name="text-red-500"
                                    ),
                                    rx.el.p(
                                        f"Failed: {AIModelState.openrouter_test_result['error']}",
                                        class_name="text-sm text-red-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                            ),
                            None,
                        ),
                    ),
                    rx.el.div(
                        api_key_input(
                            "Mistral API Key",
                            "mistral_api_key",
                            SettingsState.mistral_api_key,
                            SettingsState.set_mistral_api_key,
                            SettingsState.show_mistral_key,
                            lambda: SettingsState.toggle_visibility("mistral"),
                        ),
                        rx.el.button(
                            "Test Key",
                            on_click=lambda: AIModelState.test_api_key("mistral"),
                            class_name="mt-2 w-full bg-gray-200 text-gray-700 p-2 rounded-md hover:bg-gray-300 disabled:bg-gray-100",
                            disabled=~SettingsState.is_mistral_key_set
                            | AIModelState.is_testing_mistral,
                        ),
                        rx.cond(
                            AIModelState.is_testing_mistral,
                            rx.el.div(
                                rx.spinner(class_name="h-4 w-4 text-gray-500"),
                                rx.el.p(
                                    "Testing...", class_name="text-sm text-gray-500"
                                ),
                                class_name="flex items-center gap-2 mt-2",
                            ),
                            None,
                        ),
                        rx.cond(
                            AIModelState.mistral_test_result,
                            rx.cond(
                                AIModelState.mistral_test_result["success"],
                                rx.el.div(
                                    rx.icon(
                                        "check_check",
                                        size=16,
                                        class_name="text-green-500",
                                    ),
                                    rx.el.p(
                                        "Success! Key is valid.",
                                        class_name="text-sm text-green-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                                rx.el.div(
                                    rx.icon(
                                        "circle_x", size=16, class_name="text-red-500"
                                    ),
                                    rx.el.p(
                                        f"Failed: {AIModelState.mistral_test_result['error']}",
                                        class_name="text-sm text-red-600",
                                    ),
                                    class_name="flex items-center gap-2 mt-2",
                                ),
                            ),
                            None,
                        ),
                    ),
                ),
                class_name="p-6 bg-white rounded-lg border",
            ),
            class_name="space-y-6 max-w-2xl mx-auto",
        ),
        class_name="w-full",
    )
    return page_layout(content)