import reflex as rx
from app.states.settings_state import SettingsState
from app.states.chat_state import ChatState
from app.components.sidebar import page_layout
from app.pages.settings import settings_page


def quick_link_card(icon: str, title: str, description: str, href: str) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(icon, class_name="h-8 w-8 text-blue-500"),
            rx.el.h3(title, class_name="text-lg font-semibold text-gray-800"),
            rx.el.p(description, class_name="text-sm text-gray-500"),
            class_name="flex flex-col items-start gap-2",
        ),
        href=href,
        class_name="block p-6 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-lg transition-shadow duration-200",
    )


def index() -> rx.Component:
    main_content = rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Shopify AI Management", class_name="text-4xl font-bold text-gray-900"
            ),
            rx.el.p(
                "Your intelligent assistant for managing your Shopify store.",
                class_name="text-lg text-gray-600 mt-2",
            ),
            class_name="text-center",
        ),
        rx.el.div(
            quick_link_card(
                "message-circle",
                "AI Chat",
                "Interact with your store using natural language.",
                "/chat",
            ),
            quick_link_card(
                "settings",
                "Settings",
                "Configure API keys and store credentials.",
                "/settings",
            ),
            quick_link_card(
                "layout-dashboard",
                "Dashboard (Coming Soon)",
                "View real-time KPIs and store metrics.",
                "#",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12",
        ),
        class_name="flex flex-col items-center justify-center h-full p-8",
    )
    return page_layout(main_content)


def chat() -> rx.Component:
    main_content = rx.el.div(
        rx.el.div(
            rx.foreach(ChatState.messages, message_bubble),
            class_name="flex-1 overflow-y-auto p-4 space-y-4",
        ),
        rx.el.div(
            rx.el.form(
                rx.el.div(
                    rx.el.input(
                        name="question",
                        placeholder="Ask a question...",
                        class_name="flex-1 p-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                        disabled=ChatState.is_processing,
                        default_value=ChatState.current_question,
                        key=ChatState.current_question,
                    ),
                    rx.el.button(
                        rx.icon("arrow-up", size=20),
                        type="submit",
                        class_name="p-2 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600 disabled:bg-gray-400",
                        disabled=ChatState.is_processing,
                    ),
                    class_name="flex",
                ),
                on_submit=ChatState.answer,
                reset_on_submit=True,
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.p(
                    f"Model: {ChatState.current_model_name}",
                    class_name="text-xs text-gray-500",
                ),
                rx.cond(
                    ChatState.is_processing,
                    rx.el.div(
                        rx.spinner(class_name="h-4 w-4 text-gray-500"),
                        rx.el.p("Processing...", class_name="text-xs text-gray-500"),
                        class_name="flex items-center space-x-2",
                    ),
                    None,
                ),
                class_name="flex justify-between items-center w-full mt-1 px-1",
            ),
            class_name="p-4 border-t bg-gray-50",
        ),
        class_name="flex flex-col h-full bg-gray-100",
    )
    return page_layout(main_content)


def message_bubble(message: dict) -> rx.Component:
    is_user = message["role"] == "user"
    return rx.el.div(
        rx.el.div(
            rx.markdown(message["content"], class_name="prose text-sm"),
            class_name=rx.cond(
                is_user,
                "bg-blue-500 text-white p-3 rounded-lg max-w-lg",
                "bg-white p-3 rounded-lg max-w-lg border",
            ),
        ),
        class_name=rx.cond(is_user, "flex justify-end", "flex justify-start"),
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)
app.add_page(chat, on_load=ChatState.on_load)
app.add_page(settings_page, route="/settings")