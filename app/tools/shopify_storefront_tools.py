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

    temp_state = rx.State()
    settings = await temp_state.get_state(SettingsState)
    if not settings.is_shopify_storefront_token_set or not settings.shopify_store_url:
        logging.error("Shopify Storefront credentials are not set.")
        return (None, None)
    endpoint = f"https://{settings.shopify_store_url}/api/2024-04/graphql.json"
    headers = {
        "X-Shopify-Storefront-Access-Token": settings.shopify_storefront_token,
        "Content-Type": "application/json",
    }
    client = httpx.AsyncClient(headers=headers)
    return (client, endpoint)


class ShopifyStorefrontTools(Toolkit):
    """A toolkit for interacting with the Shopify Storefront API."""

    def __init__(self, **kwargs):
        tools: list = [self.search_products, self.get_product_by_handle]
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