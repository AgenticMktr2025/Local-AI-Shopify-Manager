import reflex as rx
from app.states.settings_state import SettingsState


def nav_item(
    icon: str, text: str, href: str, is_active: bool, is_disabled: bool = False
) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-5 w-5"),
        rx.el.span(text, class_name="font-medium"),
        href=href,
        class_name=rx.cond(
            is_active,
            "flex items-center gap-3 rounded-lg bg-gray-100 px-3 py-2 text-gray-900 transition-all hover:text-gray-900",
            "flex items-center gap-3 rounded-lg px-3 py-2 text-gray-500 transition-all hover:text-gray-900",
        ),
        disabled=is_disabled,
    )


def sidebar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("store", class_name="h-6 w-6 text-blue-600"),
                    rx.el.span("Shopify AI", class_name="sr-only"),
                    href="#",
                    class_name="flex items-center gap-2 font-semibold",
                ),
                class_name="flex h-14 items-center border-b px-6 lg:h-[60px]",
            ),
            rx.el.div(
                rx.el.nav(
                    nav_item(
                        "home", "Dashboard", "/", rx.State.router.page.path == "/"
                    ),
                    nav_item(
                        "message-circle",
                        "Chat",
                        "/chat",
                        rx.State.router.page.path == "/chat",
                    ),
                    nav_item(
                        "settings",
                        "Settings",
                        "/settings",
                        rx.State.router.page.path == "/settings",
                    ),
                    class_name="grid items-start px-4 text-sm font-medium",
                ),
                class_name="flex-1 overflow-auto py-2",
            ),
        ),
        class_name="hidden border-r bg-gray-50/40 md:block w-64",
    )


def page_layout(main_content: rx.Component) -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            rx.el.header(
                rx.el.div(),
                class_name="flex h-14 lg:h-[60px] items-center gap-4 border-b bg-gray-100/40 px-6",
            ),
            rx.el.main(main_content, class_name="flex-1 p-4 md:p-6"),
            class_name="flex flex-col flex-1",
        ),
        class_name="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]",
    )