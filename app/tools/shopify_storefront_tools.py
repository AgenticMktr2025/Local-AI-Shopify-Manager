import reflex as rx
import logging
import json
import httpx
from agno.tools.toolkit import Toolkit
from typing import Optional


async def get_storefront_api_client() -> (
    tuple[httpx.AsyncClient, str] | tuple[None, None]
):
    """Creates an httpx client configured for the Shopify Storefront API."""
    from app.states.settings_state import SettingsState

    settings = rx.State.get_state(SettingsState)
    if not settings:
        settings = SettingsState()
    store_url = settings.shopify_store_url
    storefront_token = settings.shopify_storefront_token
    if ~storefront_token | ~store_url:
        logging.error("Shopify Storefront credentials are not set in SettingsState.")
        return (None, None)
    endpoint = f"https://{store_url}/api/2024-04/graphql.json"
    headers = {
        "X-Shopify-Storefront-Access-Token": storefront_token,
        "Content-Type": "application/json",
    }
    client = httpx.AsyncClient(headers=headers)
    return (client, endpoint)


class ShopifyStorefrontTools(Toolkit):
    """A toolkit for interacting with the Shopify Storefront API."""

    def __init__(self, **kwargs):
        tools: list = [
            self.search_products,
            self.get_product_by_handle,
            self.create_checkout,
            self.get_checkout,
            self.update_checkout,
            self.complete_checkout,
            self.apply_discount_to_checkout,
            self.create_customer_account,
            self.update_customer_account,
            self.reset_customer_password,
        ]
        super().__init__(name="shopify_storefront", tools=tools, **kwargs)

    async def _execute_query(
        self, tool_name: str, query: str, variables: Optional[dict] = None
    ) -> str:
        """Executes a GraphQL query against the Storefront API."""
        client, endpoint = await get_storefront_api_client()
        if not client or not endpoint:
            return json.dumps(
                {
                    "success": False,
                    "error": "Storefront API client not available. Check credentials.",
                    "tool": tool_name,
                }
            )
        try:
            payload = {"query": query, "variables": variables or {}}
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            if "errors" in result:
                return json.dumps(
                    {"success": False, "error": result["errors"], "tool": tool_name}
                )
            return json.dumps(
                {"success": True, "data": result["data"], "tool": tool_name}
            )
        except httpx.HTTPStatusError as e:
            logging.exception(
                f"Shopify Storefront query failed for tool {tool_name}: {e.response.text}"
            )
            return json.dumps(
                {
                    "success": False,
                    "error": f"HTTP Error: {e.response.status_code} - {e.response.text}",
                    "tool": tool_name,
                }
            )
        except Exception as e:
            logging.exception(
                f"Shopify Storefront query failed for tool {tool_name}: {e}"
            )
            return json.dumps({"success": False, "error": str(e), "tool": tool_name})
        finally:
            if client:
                await client.aclose()

    async def search_products(self, search_term: str, limit: int = 10) -> str:
        """
        [Storefront] - Search for products available in the online store.

        Description: Use this to find products from a customer's perspective. It's great for checking public-facing product availability, titles, and handles.

        Example Usage:
        - "Are there any 'black t-shirts' in the store?" -> search_products(search_term="black t-shirt")
        - "Find products matching 'summer collection'" -> search_products(search_term="summer collection")

        Args:
            search_term (str): The keyword to search for in product titles, tags, etc.
            limit (int): Maximum number of products to return (1-250).

        Returns:
            JSON string with a list of publicly available products including title and handle.
        """
        graphql_query = """
        query searchProducts($limit: Int!, $query: String!) {
          products(first: $limit, query: $query) {
            edges {
              node {
                id
                title
                handle
                onlineStoreUrl
              }
            }
          }
        }
        """
        variables = {"limit": limit, "query": search_term}
        return await self._execute_query(
            "search_products", graphql_query, variables=variables
        )

    async def get_product_by_handle(self, handle: str) -> str:
        """
        [Storefront] - Get public product details by its URL handle.

        Description: Retrieves detailed, public-facing information for a single product using its user-friendly URL handle (e.g., 'classic-leather-jacket').

        Example Usage:
        - "Show me the product with handle 'classic-leather-jacket'" -> get_product_by_handle(handle="classic-leather-jacket")

        Args:
            handle (str): The product's URL handle.

        Returns:
            JSON string with public product details like title, description, price, and variants.
        """
        graphql_query = """
        query getProductByHandle($handle: String!) {
          product(handle: $handle) {
            id
            title
            descriptionHtml
            onlineStoreUrl
            priceRange {
              minVariantPrice {
                amount
                currencyCode
              }
            }
            variants(first: 10) {
              edges {
                node {
                  id
                  title
                  price { amount currencyCode }
                  availableForSale
                }
              }
            }
          }
        }
        """
        variables = {"handle": handle}
        return await self._execute_query(
            "get_product_by_handle", graphql_query, variables=variables
        )

    async def create_checkout(
        self, line_items: list[dict], email: Optional[str] = None
    ) -> str:
        """
        [Storefront - Checkout] - Create a new checkout session.

        Description: Initializes a checkout with a list of line items (variant ID and quantity). This is the first step in programmatically creating a cart for a customer.

        Required Permissions: unauthenticated_write_checkouts

        Example Usage:
        - "Start a checkout for a customer with variant 'gid://.../Variant/1' quantity 1." -> create_checkout(line_items=[{{"variantId": "gid://.../Variant/1", "quantity": 1}}])

        Args:
            line_items (list[dict]): A list of dictionaries, each with 'variantId' and 'quantity'.
            email (Optional[str]): The customer's email to associate with the checkout.

        Returns:
            JSON string with the checkout ID and web URL.
        """
        input_vars = {"lineItems": line_items}
        if email:
            input_vars["email"] = email
        graphql_mutation = """
        mutation checkoutCreate($input: CheckoutCreateInput!) {
          checkoutCreate(input: $input) {
            checkout {
              id
              webUrl
            }
            checkoutUserErrors {
              field
              message
            }
          }
        }
        """
        return await self._execute_query(
            "checkoutCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_checkout(self, checkout_id: str) -> str:
        """
        [Storefront - Checkout] - Retrieve a checkout by its ID.

        Description: Fetches the current state of a checkout, including line items and totals.

        Required Permissions: unauthenticated_read_checkouts

        Example Usage:
        - "Get the details for checkout 'gid://.../Checkout/abc'." -> get_checkout(checkout_id="gid://.../Checkout/abc")

        Args:
            checkout_id (str): The GraphQL ID of the checkout.

        Returns:
            JSON string with checkout details.
        """
        graphql_query = f'\n        {{\n          node(id: "{checkout_id}") {{\n            ... on Checkout {{\n              id\n              webUrl\n              totalPriceV2 {{\n                amount\n                currencyCode\n              }}\n              lineItems(first: 10) {{\n                edges {{\n                  node {{\n                    title\n                    quantity\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return await self._execute_query("get_checkout", graphql_query)

    async def update_checkout(self, checkout_id: str, line_items: list[dict]) -> str:
        """
        [Storefront - Checkout] - Update the line items in a checkout.

        Description: Replaces the existing line items in a checkout with a new list.

        Required Permissions: unauthenticated_write_checkouts

        Example Usage:
        - "Update checkout 'gid://.../Checkout/abc' to only contain variant 'gid://.../Variant/2'." -> update_checkout(checkout_id="gid://.../abc", line_items=[{{"variantId": "gid://.../Variant/2", "quantity": 1}}])

        Args:
            checkout_id (str): The GraphQL ID of the checkout.
            line_items (list[dict]): The new list of line items.

        Returns:
            JSON string with the updated checkout details.
        """
        input_vars = {"checkoutId": checkout_id, "lineItems": line_items}
        graphql_mutation = """
        mutation checkoutLineItemsReplace($checkoutId: ID!, $lineItems: [CheckoutLineItemInput!]!) {
          checkoutLineItemsReplace(checkoutId: $checkoutId, lineItems: $lineItems) {
            checkout {
              id
              webUrl
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return await self._execute_query(
            "checkoutLineItemsReplace", graphql_mutation, variables=input_vars
        )

    async def complete_checkout(self, checkout_id: str, payment_token: str) -> str:
        """
        [Storefront - Checkout] - This tool is a placeholder for completing a checkout.

        Description: Completing a checkout requires a vaulted payment token from a payment provider, which is beyond the scope of this tool. This function returns a message indicating the next steps.

        Returns:
            JSON string explaining how to complete a checkout.
        """
        return json.dumps(
            {
                "success": False,
                "error": "Completing a checkout requires a payment token from a provider like Shopify Payments. This action cannot be fully performed here.",
                "tool": "complete_checkout",
            }
        )

    async def apply_discount_to_checkout(
        self, checkout_id: str, discount_code: str
    ) -> str:
        """
        [Storefront - Checkout] - Apply a discount code to a checkout.

        Description: Applies a discount code to the specified checkout.

        Required Permissions: unauthenticated_write_checkouts

        Example Usage:
        - "Apply code 'SAVE10' to checkout 'gid://.../Checkout/abc'." -> apply_discount_to_checkout(checkout_id="gid://.../abc", discount_code="SAVE10")

        Args:
            checkout_id (str): The GraphQL ID of the checkout.
            discount_code (str): The discount code to apply.

        Returns:
            JSON string with the checkout, reflecting the applied discount.
        """
        graphql_mutation = """
        mutation checkoutDiscountCodeApplyV2($checkoutId: ID!, $discountCode: String!) {
          checkoutDiscountCodeApplyV2(checkoutId: $checkoutId, discountCode: $discountCode) {
            checkout {
              id
              webUrl
            }
            checkoutUserErrors {
              field
              message
            }
          }
        }
        """
        variables = {"checkoutId": checkout_id, "discountCode": discount_code}
        return await self._execute_query(
            "checkoutDiscountCodeApplyV2", graphql_mutation, variables=variables
        )

    async def create_customer_account(
        self, email: str, password: str, first_name: Optional[str] = None
    ) -> str:
        """
        [Storefront - Customers] - Create a new customer account.

        Description: Registers a new customer in the store.

        Required Permissions: unauthenticated_write_customers

        Example Usage:
        - "Create an account for 'test@example.com'." -> create_customer_account(email="test@example.com", password="strong-password")

        Args:
            email (str): The customer's email address.
            password (str): The customer's chosen password.
            first_name (Optional[str]): The customer's first name.

        Returns:
            JSON string with the new customer account details or an error message.
        """
        input_vars = {"email": email, "password": password}
        if first_name:
            input_vars["firstName"] = first_name
        graphql_mutation = """
        mutation customerCreate($input: CustomerCreateInput!) {
          customerCreate(input: $input) {
            customer {
              id
              email
            }
            customerUserErrors {
              field
              message
            }
          }
        }
        """
        return await self._execute_query(
            "customerCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_customer_account(
        self, customer_access_token: str, **kwargs
    ) -> str:
        """
        [Storefront - Customers] - Update a customer's account information.

        Description: Updates the profile of a logged-in customer using their access token.

        Required Permissions: unauthenticated_write_customers

        Example Usage:
        - "Update the customer's first name to 'Jane'." -> update_customer_account(customer_access_token="...", firstName="Jane")

        Args:
            customer_access_token (str): The access token for the authenticated customer.
            **kwargs: Fields to update (e.g., firstName, lastName, email, password).

        Returns:
            JSON string with the updated customer data or an error message.
        """
        customer_input = {
            key: value for key, value in kwargs.items() if value is not None
        }
        graphql_mutation = """
        mutation customerUpdate($customerAccessToken: String!, $customer: CustomerUpdateInput!) {
          customerUpdate(customerAccessToken: $customerAccessToken, customer: $customer) {
            customer {
              id
            }
            customerUserErrors {
              field
              message
            }
          }
        }
        """
        variables = {
            "customerAccessToken": customer_access_token,
            "customer": customer_input,
        }
        return await self._execute_query(
            "customerUpdate", graphql_mutation, variables=variables
        )

    async def reset_customer_password(self, email: str) -> str:
        """
        [Storefront - Customers] - Send a password reset email to a customer.

        Description: Triggers the password reset process for a given email address.

        Required Permissions: unauthenticated_write_customers

        Example Usage:
        - "Send a password reset link to 'forgot@example.com'." -> reset_customer_password(email="forgot@example.com")

        Args:
            email (str): The email address of the customer who needs a password reset.

        Returns:
            JSON string confirming the request or an error message.
        """
        graphql_mutation = """
        mutation customerRecover($email: String!) {
          customerRecover(email: $email) {
            customerUserErrors {
              field
              message
            }
          }
        }
        """
        return await self._execute_query(
            "customerRecover", graphql_mutation, variables={"email": email}
        )