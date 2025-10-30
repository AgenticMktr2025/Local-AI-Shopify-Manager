import reflex as rx
import shopify
import logging
import json
from agno.tools.toolkit import Toolkit
from typing import Optional, Literal


async def get_shopify_session() -> shopify.Session | None:
    """Creates and activates a Shopify API session."""
    from app.states.settings_state import SettingsState

    temp_state = rx.State()
    settings = await temp_state.get_state(SettingsState)
    if not settings.are_shopify_credentials_set:
        logging.error("Shopify credentials are not set in SettingsState.")
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
    """A toolkit for interacting with the Shopify Admin API using GraphQL."""

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

    def _execute_query(
        self, tool_name: str, query: str, variables: Optional[dict] = None
    ) -> str:
        """Executes a GraphQL query and returns a structured JSON string."""
        try:
            raw_result = shopify.GraphQL().execute(query, variables=variables)
            result = json.loads(raw_result)
            if "errors" in result or "userErrors" in result.get("data", {}).get(
                tool_name, {}
            ):
                error_details = result.get("errors") or result.get("data", {}).get(
                    tool_name, {}
                ).get("userErrors")
                return json.dumps(
                    {"success": False, "error": str(error_details), "tool": tool_name}
                )
            return json.dumps(
                {"success": True, "data": result["data"], "tool": tool_name}
            )
        except Exception as e:
            logging.exception(f"Shopify GraphQL query failed for tool {tool_name}: {e}")
            return json.dumps({"success": False, "error": str(e), "tool": tool_name})
        finally:
            shopify.ShopifyResource.clear_session()

    async def get_products(
        self, search_title: Optional[str] = None, limit: int = 10
    ) -> str:
        """
        [Product Management] - Retrieve products from your Shopify store.

        Description: Fetches a list of products, optionally filtering by title. Use this to search inventory or check product details.

        Required Permissions: read_products

        Example Usage:
        - "Find products with 'shirt' in the title" -> get_products(search_title="shirt", limit=10)
        - "Show me all active products" -> get_products(limit=50)

        Args:
            search_title (Optional[str]): Keyword to filter product titles by.
            limit (int): Max number of products to return (1-250).

        Returns:
            JSON string with a list of products including id, title, handle, status, and inventory.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_products",
                }
            )
        query_filter = f"title:*{search_title}*" if search_title else ""
        graphql_query = f'\n        {{\n          products(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                title\n                handle\n                status\n                totalInventory\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_products", graphql_query)

    async def get_product_by_id(self, product_id: str) -> str:
        """
        [Product Management] - Get a specific product by its full GraphQL ID.

        Description: Retrieves detailed information for a single product using its GID.

        Required Permissions: read_products

        Example Usage:
        - "Show me details for product 'gid://shopify/Product/12345'." -> get_product_by_id(product_id="gid://shopify/Product/12345")

        Args:
            product_id (str): The full GraphQL ID of the product.

        Returns:
            JSON string with the product's details, including description, vendor, and type.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_product_by_id",
                }
            )
        graphql_query = f'\n        {{\n          product(id: "{product_id}") {{\n            id\n            title\n            descriptionHtml\n            status\n            vendor\n            productType\n            totalInventory\n          }}\n        }}\n        '
        return self._execute_query("get_product_by_id", graphql_query)

    async def create_product(
        self,
        title: str,
        vendor: str,
        product_type: str,
        description_html: str,
        tags: Optional[str] = None,
        status: Literal["ACTIVE", "DRAFT", "ARCHIVED"] = "DRAFT",
    ) -> str:
        """
        [Product Management] - Create a new product in the store.

        Description: Adds a new product to the Shopify catalog.

        Required Permissions: write_products

        Example Usage:
        - "Create a draft product named 'New T-Shirt' from 'MyBrand'." -> create_product(title="New T-Shirt", vendor="MyBrand", ...)

        Args:
            title (str): The title of the product.
            vendor (str): The vendor of the product.
            product_type (str): The type of product.
            description_html (str): Product description in HTML format.
            tags (Optional[str]): A comma-separated string of tags.
            status (Literal): The status of the product. Can be ACTIVE, DRAFT, or ARCHIVED.

        Returns:
            JSON string with the new product's ID or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_product",
                }
            )
        input_vars = {
            "title": title,
            "vendor": vendor,
            "productType": product_type,
            "descriptionHtml": description_html,
            "status": status,
        }
        if tags:
            input_vars["tags"] = [tag.strip() for tag in tags.split(",")]
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
        return self._execute_query(
            "productCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_customers(
        self, search_query: Optional[str] = None, limit: int = 10
    ) -> str:
        """
        [Customer Management] - Get a list of customers.

        Description: Retrieves customers, with an option to search by name or email.

        Required Permissions: read_customers

        Example Usage:
        - "Find customers named John Doe." -> get_customers(search_query="John Doe")
        - "List the last 5 customers." -> get_customers(limit=5)

        Args:
            search_query (Optional[str]): A name or email to search for.
            limit (int): The maximum number of customers to return (1-250).

        Returns:
            JSON string with customer data including name, email, and phone.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_customers",
                }
            )
        graphql_query = f'''\n        {{\n          customers(first: {limit}, query: "{search_query or ""}") {{\n            edges {{\n              node {{\n                id\n                firstName\n                lastName\n                email\n                phone\n              }}\n            }}\n          }}\n        }}\n        '''
        return self._execute_query("get_customers", graphql_query)

    async def get_customer_orders(self, customer_id: str, limit: int = 10) -> str:
        """
        [Customer Management] - Get recent orders for a specific customer.

        Description: Fetches orders for a customer using their GraphQL ID (GID).

        Required Permissions: read_orders, read_customers

        Example Usage:
        - "Show last 5 orders for customer 'gid://shopify/Customer/12345'." -> get_customer_orders(customer_id="gid://shopify/Customer/12345", limit=5)

        Args:
            customer_id (str): The full GraphQL ID of the customer.
            limit (int): The maximum number of orders to return (1-250).

        Returns:
            A JSON string with the customer's orders or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_customer_orders",
                }
            )
        graphql_query = f'\n        {{\n          customer(id: "{customer_id}") {{\n            orders(first: {limit}) {{\n              edges {{\n                node {{\n                  id\n                  name\n                  totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n                  displayFinancialStatus\n                  displayFulfillmentStatus\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_customer_orders", graphql_query)

    async def update_customer(self, customer_id: str, **kwargs) -> str:
        """
        [Customer Management] - Update a customer's information.

        Description: Updates a customer's profile details using keyword arguments.

        Required Permissions: write_customers

        Example Usage:
        - "Update customer 'gid://shopify/Customer/12345' email to 'new@example.com'." -> update_customer(customer_id="gid://...", email="new@example.com")

        Args:
            customer_id (str): The GraphQL ID of the customer to update.
            **kwargs: Fields to update (e.g., firstName, email, note).

        Returns:
            JSON string with the updated customer data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_customer",
                }
            )
        input_vars = {"id": customer_id}
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
        return self._execute_query(
            "customerUpdate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_orders(
        self, financial_status: Optional[str] = None, limit: int = 10
    ) -> str:
        """
        [Order Management] - Get a list of orders.

        Description: Retrieves orders, with optional filtering by financial status.

        Required Permissions: read_orders

        Example Usage:
        - "Get the 10 most recent pending orders." -> get_orders(financial_status="pending", limit=10)

        Args:
            financial_status (Optional[str]): Filter by status (e.g., 'pending', 'paid').
            limit (int): The maximum number of orders to return (1-250).

        Returns:
            JSON string with order data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_orders",
                }
            )
        query_filter = (
            f"financial_status:{financial_status}" if financial_status else ""
        )
        graphql_query = f'\n        {{\n          orders(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                name\n                displayFinancialStatus\n                displayFulfillmentStatus\n                totalPriceSet {{\n                  shopMoney {{\n                    amount\n                    currencyCode\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_orders", graphql_query)

    async def get_order_by_id(self, order_id: str) -> str:
        """
        [Order Management] - Get a specific order by its GraphQL ID.

        Description: Retrieves detailed information for a single order using its GID.

        Required Permissions: read_orders

        Example Usage:
        - "Get details for order 'gid://shopify/Order/12345'." -> get_order_by_id(order_id="gid://shopify/Order/12345")

        Args:
            order_id (str): The full GraphQL ID of the order.

        Returns:
            JSON string with the order's details.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_order_by_id",
                }
            )
        graphql_query = f'\n        {{\n          order(id: "{order_id}") {{\n            id\n            name\n            note\n            displayFinancialStatus\n            displayFulfillmentStatus\n            totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n            customer {{ id firstName lastName email }}\n          }}\n        }}\n        '
        return self._execute_query("get_order_by_id", graphql_query)

    async def update_order(self, order_id: str, **kwargs) -> str:
        """
        [Order Management] - Update an order's information.

        Description: Updates an order using its GID and keyword arguments for fields.

        Required Permissions: write_orders

        Example Usage:
        - "Add a note 'fragile item' to order 'gid://shopify/Order/12345'." -> update_order(order_id="gid://...", note="fragile item")

        Args:
            order_id (str): The GraphQL ID of the order to update.
            **kwargs: Fields to update (e.g., note, tags, shippingAddress).

        Returns:
            JSON string with the updated order data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_order",
                }
            )
        input_vars = {"id": order_id}
        valid_args = ["note", "tags", "email", "customAttributes", "shippingAddress"]
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
        return self._execute_query(
            "orderUpdate", graphql_mutation, variables={"input": input_vars}
        )