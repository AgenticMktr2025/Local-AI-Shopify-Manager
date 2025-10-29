import reflex as rx
import shopify
import logging
import json
from agno.tools.toolkit import Toolkit
from typing import Optional


async def get_shopify_session() -> shopify.Session | None:
    from app.states.settings_state import SettingsState

    temp_state = rx.State()
    settings = await temp_state.get_state(SettingsState)
    if not settings.are_shopify_credentials_set:
        logging.error("Shopify credentials are not set.")
        return None
    try:
        session = shopify.Session(
            settings.shopify_store_url, "2024-04", settings.shopify_access_token
        )
        shopify.ShopifyResource.activate_session(session)
        return session
    except Exception as e:
        logging.exception(f"Failed to create Shopify session: {e}")
        return None


class ShopifyTools(Toolkit):
    """Tools for interacting with the Shopify Admin API."""

    def __init__(self, **kwargs):
        tools: list = [
            self.get_products,
            self.get_product_by_id,
            self.create_product,
            self.get_customers,
            self.get_customer_orders,
            self.update_customer,
            self.get_orders,
            self.get_order_by_id,
            self.update_order,
        ]
        super().__init__(name="shopify", tools=tools, **kwargs)

    async def get_products(
        self, search_title: Optional[str] = None, limit: int = 10
    ) -> str:
        """Get all products or search by title."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            query_filter = f"title:*{search_title}*" if search_title else ""
            graphql_query = f'\n            {{\n              products(first: {limit}, query: "{query_filter}") {{\n                edges {{\n                  node {{\n                    id\n                    title\n                    handle\n                    status\n                    totalInventory\n                  }}\n                }}\n              }}\n            }}\n            '
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting products: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_product_by_id(self, product_id: str) -> str:
        """Get a specific product by ID. Use the full GID, e.g., 'gid://shopify/Product/12345'."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            graphql_query = f'\n            {{\n              product(id: "{product_id}") {{\n                id\n                title\n                descriptionHtml\n                status\n                vendor\n                productType\n                totalInventory\n              }}\n            }}\n            '
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting product by id: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def create_product(
        self,
        title: str,
        description_html: str,
        vendor: str,
        product_type: str,
        tags: str,
        status: str = "DRAFT",
    ) -> str:
        """Create a new product in the store."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            input_vars = {
                "title": title,
                "descriptionHtml": description_html,
                "vendor": vendor,
                "productType": product_type,
                "tags": [tag.strip() for tag in tags.split(",")],
                "status": status.upper(),
            }
            graphql_mutation = """
            mutation productCreate($input: ProductInput!) {
              productCreate(input: $input) {
                product {
                  id
                  title
                  status
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            result = shopify.GraphQL().execute(
                graphql_mutation, variables={"input": input_vars}
            )
            return str(result)
        except Exception as e:
            logging.exception(f"Error creating product: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_customers(
        self, search_query: Optional[str] = None, limit: int = 10
    ) -> str:
        """Get customers or search by name/email."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            graphql_query = f'''\n            {{\n              customers(first: {limit}, query: "{search_query or ""}") {{\n                edges {{\n                  node {{\n                    id\n                    firstName\n                    lastName\n                    email\n                    phone\n                  }}\n                }}\n              }}\n            }}\n            '''
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting customers: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_customer_orders(self, customer_id: str, limit: int = 10) -> str:
        """Get orders for a specific customer by their GID."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            graphql_query = f'\n            {{\n              customer(id: "{customer_id}") {{\n                orders(first: {limit}) {{\n                  edges {{\n                    node {{\n                      id\n                      name\n                      totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n                      displayFinancialStatus\n                      displayFulfillmentStatus\n                    }}\n                  }}\n                }}\n              }}\n            }}\n            '
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting customer orders: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def update_customer(self, id: str, **kwargs) -> str:
        """Update a customer's information. Pass updates as keyword arguments (e.g., firstName='John', email='new@email.com')."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            input_vars = {"id": id}
            valid_args = [
                "firstName",
                "lastName",
                "email",
                "phone",
                "tags",
                "note",
                "taxExempt",
            ]
            for key, value in kwargs.items():
                if key in valid_args and value is not None:
                    input_vars[key] = value
            graphql_mutation = """
            mutation customerUpdate($input: CustomerInput!) {
              customerUpdate(input: $input) {
                customer {
                  id
                  firstName
                  lastName
                  email
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            result = shopify.GraphQL().execute(
                graphql_mutation, variables={"input": input_vars}
            )
            return str(result)
        except Exception as e:
            logging.exception(f"Error updating customer: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_orders(self, status: str = "any", limit: int = 10) -> str:
        """Get orders with optional filtering by status."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            graphql_query = f'\n            {{\n              orders(first: {limit}, query: "status:{status}") {{\n                edges {{\n                  node {{\n                    id\n                    name\n                    displayFinancialStatus\n                    displayFulfillmentStatus\n                    totalPriceSet {{\n                      shopMoney {{\n                        amount\n                        currencyCode\n                      }}\n                    }}\n                  }}\n                }}\n              }}\n            }}\n            '
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting orders: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_order_by_id(self, order_id: str) -> str:
        """Get a specific order by its GID, e.g., 'gid://shopify/Order/12345'."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            graphql_query = f'\n            {{\n              order(id: "{order_id}") {{\n                id\n                name\n                note\n                displayFinancialStatus\n                displayFulfillmentStatus\n                totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n                customer {{ id firstName lastName email }}\n              }}\n            }}\n            '
            result = shopify.GraphQL().execute(graphql_query)
            return str(result)
        except Exception as e:
            logging.exception(f"Error getting order by id: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()

    async def update_order(self, id: str, **kwargs) -> str:
        """Update an order. Pass updates as keyword arguments (e.g., note='New note', tags=['newtag'])."""
        session = await get_shopify_session()
        if not session:
            return "Error: Shopify session not available. Check credentials."
        try:
            input_vars = {"id": id}
            valid_args = [
                "note",
                "tags",
                "email",
                "customAttributes",
                "shippingAddress",
            ]
            for key, value in kwargs.items():
                if key in valid_args and value is not None:
                    input_vars[key] = value
            graphql_mutation = """
            mutation orderUpdate($input: OrderInput!) {
              orderUpdate(input: $input) {
                order {
                  id
                  name
                  note
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            result = shopify.GraphQL().execute(
                graphql_mutation, variables={"input": input_vars}
            )
            return str(result)
        except Exception as e:
            logging.exception(f"Error updating order: {e}")
            return f"Error: {e}"
        finally:
            shopify.ShopifyResource.clear_session()