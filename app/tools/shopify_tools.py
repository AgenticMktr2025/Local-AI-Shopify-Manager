import reflex as rx
import shopify
import logging
import json
from agno.tools.toolkit import Toolkit
from typing import Optional, Literal


async def get_shopify_session(
    store_url: str, access_token: str
) -> shopify.Session | None:
    """Creates and activates a Shopify API session."""
    if not store_url or not access_token:
        logging.error("Shopify credentials were not provided.")
        return None
    try:
        session = shopify.Session(store_url, "2024-04", access_token)
        shopify.ShopifyResource.activate_session(session)
        return session
    except Exception as e:
        logging.exception(f"Failed to create Shopify session: {e}")
        return None


class ShopifyTools(Toolkit):
    """A toolkit for interacting with the Shopify Admin API using GraphQL."""

    def __init__(self, store_url: str, access_token: str, **kwargs):
        self.store_url = store_url
        self.access_token = access_token
        tools: list = [
            self.get_products,
            self.get_product_by_id,
            self.create_product,
            self.create_product_variant,
            self.update_product_variant,
            self.delete_product_variant,
            self.get_product_metafields,
            self.set_product_metafield,
            self.get_inventory_levels,
            self.adjust_inventory_level,
            self.create_collection,
            self.add_products_to_collection,
            self.get_customers,
            self.get_customer_orders,
            self.update_customer,
            self.get_orders,
            self.get_order_by_id,
            self.update_order,
            self.cancel_order,
            self.create_fulfillment,
            self.update_fulfillment_tracking,
            self.create_refund,
            self.get_returns,
            self.get_return_by_id,
            self.create_return,
            self.approve_return,
            self.decline_return,
            self.close_return,
            self.get_draft_orders,
            self.get_draft_order_by_id,
            self.create_draft_order,
            self.update_draft_order,
            self.complete_draft_order,
            self.send_draft_order_invoice,
            self.delete_draft_order,
            self.create_basic_discount_code,
            self.get_discount_codes,
            self.update_basic_discount_code,
            self.delete_discount_code,
            self.create_gift_card,
            self.get_locations,
            self.get_location_by_id,
            self.activate_location,
            self.deactivate_location,
            self.create_staged_upload,
            self.get_files,
            self.file_create,
            self.delete_files,
            self.get_reports,
            self.get_report_by_id,
            self.get_blogs,
            self.get_articles,
            self.get_article_by_id,
            self.create_article,
            self.update_article,
            self.delete_article,
            self.get_pages,
            self.get_page_by_id,
            self.create_page,
            self.update_page,
            self.delete_page,
            self.get_marketing_events,
            self.get_marketing_event_by_id,
            self.create_marketing_event,
            self.update_marketing_event,
            self.delete_marketing_event,
            self.get_shipping_zones,
            self.get_shipping_zone_by_id,
            self.create_shipping_zone,
            self.update_shipping_zone,
            self.delete_shipping_zone,
            self.get_shipping_rates,
            self.create_shipping_rate,
            self.update_shipping_rate,
            self.delete_shipping_rate,
            self.get_markets,
            self.get_market_by_id,
            self.create_market,
            self.update_market,
            self.delete_market,
            self.get_market_catalogs,
            self.get_themes,
            self.get_theme_by_id,
            self.get_theme_assets,
            self.get_theme_asset,
            self.update_theme_asset,
            self.delete_theme_asset,
            self.get_translations,
            self.create_translation,
            self.update_translation,
            self.delete_translation,
            self.get_locales,
            self.get_shop_policies,
            self.update_shop_policy,
            self.update_privacy_policy,
            self.update_terms_of_service,
            self.update_refund_policy,
            self.update_shipping_policy,
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
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_products",
                }
            )
        query_filter = f"title:*{search_title}*" if search_title else ""
        graphql_query = f'\n        {{\n          products(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                title\n                handle\n                status\n                totalInventory\n                variants(first: 5) {{\n                  edges {{\n                    node {{\n                      id\n                      price\n                      sku\n                    }}\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
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
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_product_by_id",
                }
            )
        graphql_query = f'\n        {{\n          product(id: "{product_id}") {{\n            id\n            title\n            descriptionHtml\n            status\n            vendor\n            productType\n            totalInventory\n            variants(first: 10) {{\n                edges {{\n                    node {{\n                        id\n                        title\n                        price\n                        sku\n                        availableForSale\n                        inventoryQuantity\n                    }}\n                }}\n            }}\n          }}\n        }}\n        '
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
        session = await get_shopify_session(self.store_url, self.access_token)
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

    async def create_product_variant(
        self, product_id: str, options: list[str], price: str, sku: str
    ) -> str:
        """
        [Product Management] - Create a new variant for a product.

        Description: Adds a new variant (e.g., size, color) to an existing product.

        Required Permissions: write_products

        Example Usage:
        - "Add a 'Small' variant for product 'gid://shopify/Product/123' with price 29.99 and SKU 'TS-SM'." -> create_product_variant(product_id="gid://shopify/Product/123", options=["Small"], price="29.99", sku="TS-SM")

        Args:
            product_id (str): The GraphQL ID of the product.
            options (list[str]): A list of option values for the variant (e.g., ['Small', 'Red']).
            price (str): The price of the variant.
            sku (str): The Stock Keeping Unit for the variant.

        Returns:
            JSON string with the new variant's ID or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_product_variant",
                }
            )
        input_vars = {
            "productId": product_id,
            "options": options,
            "price": price,
            "sku": sku,
        }
        graphql_mutation = """
        mutation productVariantCreate($input: ProductVariantInput!) {
          productVariantCreate(input: $input) {
            productVariant {
              id
              title
              price
              sku
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "productVariantCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_product_variant(self, variant_id: str, **kwargs) -> str:
        """
        [Product Management] - Update an existing product variant.

        Description: Modifies properties of a product variant like price, SKU, or inventory.

        Required Permissions: write_products

        Example Usage:
        - "Update the price of variant 'gid://shopify/ProductVariant/456' to 32.50." -> update_product_variant(variant_id="gid://shopify/ProductVariant/456", price="32.50")

        Args:
            variant_id (str): The GraphQL ID of the product variant.
            **kwargs: Fields to update (e.g., price, sku, options).

        Returns:
            JSON string with the updated variant data or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_product_variant",
                }
            )
        input_vars = {"id": variant_id}
        valid_args = ["price", "sku", "options"]
        for key, value in kwargs.items():
            if key in valid_args and value is not None:
                input_vars[key] = value
        graphql_mutation = """
        mutation productVariantUpdate($input: ProductVariantInput!) {
          productVariantUpdate(input: $input) {
            productVariant {
              id
              title
              price
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "productVariantUpdate", graphql_mutation, variables={"input": input_vars}
        )

    async def delete_product_variant(self, product_id: str, variant_id: str) -> str:
        """
        [Product Management] - Delete a product variant from a product.

        Description: Permanently removes a variant from a product. This action cannot be undone.

        Required Permissions: write_products

        Example Usage:
        - "Delete variant 'gid://shopify/ProductVariant/456' from product 'gid://shopify/Product/123'." -> delete_product_variant(product_id="gid://...", variant_id="gid://...")

        Args:
            product_id (str): The GraphQL ID of the parent product.
            variant_id (str): The GraphQL ID of the variant to be deleted.

        Returns:
            JSON string with the ID of the deleted variant or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_product_variant",
                }
            )
        graphql_mutation = """
        mutation productVariantDelete($id: ID!, $productId: ID!) {
          productVariantDelete(id: $id, productId: $productId) {
            deletedProductVariantId
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": variant_id, "productId": product_id}
        return self._execute_query(
            "productVariantDelete", graphql_mutation, variables=variables
        )

    async def get_inventory_levels(
        self, product_variant_id: str, location_id: str
    ) -> str:
        """
        [Inventory Management] - Get inventory levels for a variant at a location.

        Description: Queries the stock quantity for a specific product variant at a given location.

        Required Permissions: read_inventory

        Example Usage:
        - "Check stock for variant 'gid://shopify/ProductVariant/456' at location 'gid://shopify/Location/789'." -> get_inventory_levels(product_variant_id="gid://...", location_id="gid://...")

        Args:
            product_variant_id (str): The GraphQL ID of the product variant.
            location_id (str): The GraphQL ID of the location.

        Returns:
            JSON string with inventory level details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_inventory_levels",
                }
            )
        graphql_query = f'\n        {{\n          productVariant(id: "{product_variant_id}") {{\n            inventoryItem {{\n              inventoryLevel(locationId: "{location_id}") {{\n                available\n                quantities(names: ["on_hand", "committed"]) {{\n                  name\n                  quantity\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_inventory_levels", graphql_query)

    async def adjust_inventory_level(
        self, inventory_item_id: str, location_id: str, available_delta: int
    ) -> str:
        """
        [Inventory Management] - Adjust the inventory level for an item.

        Description: Increases or decreases the available quantity of an inventory item at a location.

        Required Permissions: write_inventory

        Example Usage:
        - "Add 5 units of item 'gid://shopify/InventoryItem/111' to location 'gid://shopify/Location/222'." -> adjust_inventory_level(inventory_item_id="gid://...", location_id="gid://...", available_delta=5)
        - "Remove 2 units of item 'gid://shopify/InventoryItem/111' from location 'gid://shopify/Location/222'." -> adjust_inventory_level(inventory_item_id="gid://...", location_id="gid://...", available_delta=-2)

        Args:
            inventory_item_id (str): The GraphQL ID of the inventory item.
            location_id (str): The GraphQL ID of the location.
            available_delta (int): The amount to change the available quantity by (positive or negative).

        Returns:
            JSON string with the updated inventory level or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "adjust_inventory_level",
                }
            )
        input_vars = {
            "input": {
                "locationId": location_id,
                "inventoryItemId": inventory_item_id,
                "availableDelta": available_delta,
            }
        }
        graphql_mutation = """
        mutation inventoryAdjustQuantity($input: InventoryAdjustQuantityInput!) {
          inventoryAdjustQuantity(input: $input) {
            inventoryLevel {
              available
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "inventoryAdjustQuantity", graphql_mutation, variables=input_vars
        )

    async def create_collection(
        self, title: str, description_html: Optional[str] = None
    ) -> str:
        """
        [Product Management] - Create a new manual collection.

        Description: Creates a new collection for manually organizing products.

        Required Permissions: write_products

        Example Usage:
        - "Create a new collection called 'Summer Sale'." -> create_collection(title="Summer Sale")

        Args:
            title (str): The title of the collection.
            description_html (Optional[str]): An HTML description for the collection.

        Returns:
            JSON string with the new collection's ID or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_collection",
                }
            )
        input_vars = {"title": title}
        if description_html:
            input_vars["descriptionHtml"] = description_html
        graphql_mutation = """
        mutation collectionCreate($input: CollectionInput!) {
          collectionCreate(input: $input) {
            collection {
              id
              title
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "collectionCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def add_products_to_collection(
        self, collection_id: str, product_ids: list[str]
    ) -> str:
        """
        [Product Management] - Add one or more products to a manual collection.

        Description: Associates existing products with a specified collection.

        Required Permissions: write_products

        Example Usage:
        - "Add products ['gid://.../1', 'gid://.../2'] to collection 'gid://.../123'." -> add_products_to_collection(collection_id="gid://.../123", product_ids=["gid://.../1", "gid://.../2"])

        Args:
            collection_id (str): The GraphQL ID of the collection.
            product_ids (list[str]): A list of product GraphQL IDs to add.

        Returns:
            JSON string with the updated collection or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "add_products_to_collection",
                }
            )
        graphql_mutation = """
        mutation collectionAddProducts($id: ID!, $productIds: [ID!]!) {
          collectionAddProducts(id: $id, productIds: $productIds) {
            collection {
              id
              productsCount
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": collection_id, "productIds": product_ids}
        return self._execute_query(
            "collectionAddProducts", graphql_mutation, variables=variables
        )

    async def get_product_metafields(self, product_id: str, namespace: str) -> str:
        """
                [Product Management] - Retrieve metafields for a specific product.

                Description: Fetches custom data attached to a product within a given namespace.

        _Required Permissions: read_products_

                Example Usage:
                - "Get 'custom' metafields for product 'gid://.../123'." -> get_product_metafields(product_id="gid://.../123", namespace="custom")

                Args:
                    product_id (str): The GraphQL ID of the product.
                    namespace (str): The namespace of the metafields to retrieve.

                Returns:
                    JSON string with a list of metafields or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_product_metafields",
                }
            )
        graphql_query = f'\n        {{\n          product(id: "{product_id}") {{\n            metafields(namespace: "{namespace}", first: 10) {{\n              edges {{\n                node {{\n                  id\n                  namespace\n                  key\n                  value\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_product_metafields", graphql_query)

    async def set_product_metafield(
        self,
        owner_id: str,
        namespace: str,
        key: str,
        value: str,
        type: str = "single_line_text_field",
    ) -> str:
        """
        [Product Management] - Set a metafield for a product.

        Description: Creates or updates a custom data field for a product. Refer to Shopify docs for valid types.

        Required Permissions: write_products

        Example Usage:
        - "Set a metafield for product 'gid://.../123' with namespace 'specs', key 'material', and value 'cotton'." -> set_product_metafield(owner_id="gid://.../123", namespace="specs", key="material", value="cotton")

        Args:
            owner_id (str): The GraphQL ID of the product (the owner of the metafield).
            namespace (str): The namespace for the metafield (e.g., 'custom', 'specs').
            key (str): The key for the metafield (e.g., 'material', 'width').
            value (str): The value to set for the metafield.
            type (str): The type of metafield, e.g., 'single_line_text_field'.

        Returns:
            JSON string with the created/updated metafield or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "set_product_metafield",
                }
            )
        metafield_input = {
            "namespace": namespace,
            "key": key,
            "value": value,
            "type": type,
            "ownerId": owner_id,
        }
        graphql_mutation = """
        mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
          metafieldsSet(metafields: $metafields) {
            metafields {
              id
              key
              value
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "metafieldsSet",
            graphql_mutation,
            variables={"metafields": [metafield_input]},
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
        session = await get_shopify_session(self.store_url, self.access_token)
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
        session = await get_shopify_session(self.store_url, self.access_token)
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
        session = await get_shopify_session(self.store_url, self.access_token)
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

    async def get_orders(self, status: Optional[str] = None, limit: int = 10) -> str:
        """
        [Order Management] - Retrieve orders with optional filtering.

        Description: Fetches a list of orders, optionally filtering by status. Orders are sorted by creation date, with the most recent first.

        Required Permissions: read_orders

        Example Usage:
        - "Get the last 10 open orders." -> get_orders(status="open")
        - "Show me the 5 most recent orders." -> get_orders(limit=5)

        Args:
            status (Optional[str]): Filter by order status (e.g., 'open', 'closed', 'any').
            limit (int): Max number of orders to return.

        Returns:
            JSON string with a list of orders.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_orders",
                }
            )
        query_filter = f"status:{status}" if status else ""
        graphql_query = f'\n        {{\n          orders(first: {limit}, query: "{query_filter}", sortKey: PROCESSED_AT, reverse: true) {{\n            edges {{\n              node {{\n                id\n                name\n                processedAt\n                displayFinancialStatus\n                displayFulfillmentStatus\n                totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n                customer {{ id firstName lastName }}\n                lineItems(first: 5) {{\n                  edges {{\n                    node {{\n                      name\n                      quantity\n                      variant {{ title }}\n                    }}\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_orders", graphql_query)

    async def get_order_by_id(self, order_id: str) -> str:
        """
        [Order Management] - Get a specific order by its GraphQL ID.

        Description: Retrieves detailed information for a single order.

        Required Permissions: read_orders

        Example Usage:
        - "Show details for order 'gid://shopify/Order/12345'." -> get_order_by_id(order_id="gid://shopify/Order/12345")

        Args:
            order_id (str): The full GraphQL ID of the order.

        Returns:
            JSON string with order details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_order_by_id",
                }
            )
        graphql_query = f'\n        {{\n          order(id: "{order_id}") {{\n            id\n            name\n            processedAt\n            fullyPaid\n            totalPriceSet {{ shopMoney {{ amount currencyCode }} }}\n            totalShippingPriceSet {{ shopMoney {{ amount currencyCode }} }}\n            totalTaxSet {{ shopMoney {{ amount currencyCode }} }}\n            lineItems(first: 10) {{\n              edges {{\n                node {{ name quantity sku variant {{ id title }} }}\n              }}\n            }}\n            customer {{ id firstName lastName email }}\n            shippingAddress {{ address1 city provinceCode zip country }}\n            fulfillments(first: 5) {{\n                status\n                trackingInfo {{\n                    company\n                    number\n                    url\n                }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_order_by_id", graphql_query)

    async def update_order(self, order_id: str, **kwargs) -> str:
        """
        [Order Management] - Update an existing order.

        Description: Modifies properties of an order like tags or notes.

        Required Permissions: write_orders

        Example Usage:
        - "Add the 'VIP' tag to order 'gid://.../123'." -> update_order(order_id="gid://.../123", tags=["VIP"])

        Args:
            order_id (str): The GraphQL ID of the order.
            **kwargs: Fields to update (e.g., tags, note).

        Returns:
            JSON string with the updated order data.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_order",
                }
            )
        input_vars = {"id": order_id}
        if "tags" in kwargs:
            input_vars["tags"] = kwargs["tags"]
        if "note" in kwargs:
            input_vars["note"] = kwargs["note"]
        graphql_mutation = """
        mutation orderUpdate($input: OrderInput!) {
          orderUpdate(input: $input) {
            order {
              id
              tags
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

    async def cancel_order(self, order_id: str, reason: str = "CUSTOMER") -> str:
        """
        [Order Management] - Cancel an order.

        Description: Cancels an entire order. Specify a reason for cancellation.

        Required Permissions: write_orders

        Example Usage:
        - "Cancel order 'gid://.../123' because the customer requested it." -> cancel_order(order_id="gid://.../123", reason="CUSTOMER")

        Args:
            order_id (str): The GraphQL ID of the order.
            reason (str): Reason for cancellation (CUSTOMER, INVENTORY, FRAUD, OTHER). Defaults to CUSTOMER.

        Returns:
            JSON string confirming the cancellation or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "cancel_order",
                }
            )
        input_vars = {"id": order_id, "reason": reason}
        graphql_mutation = """
        mutation orderCancel($input: OrderCancelInput!) {
          orderCancel(input: $input) {
            order {
              id
              cancelledAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "orderCancel", graphql_mutation, variables={"input": input_vars}
        )

    async def create_fulfillment(
        self,
        order_id: str,
        line_items: list[dict],
        tracking_number: Optional[str] = None,
        tracking_company: Optional[str] = None,
    ) -> str:
        """
        [Fulfillment] - Create a fulfillment for an order.

        Description: Marks line items as fulfilled and optionally adds tracking information.

        Required Permissions: write_fulfillments

        Example Usage:
        - "Fulfill order 'gid://.../123' with one line item 'gid://.../Item/456'." -> create_fulfillment(order_id="gid://.../123", line_items=[{"id": "gid://.../Item/456", "quantity": 1}])

        Args:
            order_id (str): The GraphQL ID of the order.
            line_items (list[dict]): List of line item IDs and quantities to fulfill.
            tracking_number (Optional[str]): The tracking number for the shipment.
            tracking_company (Optional[str]): The shipping carrier.

        Returns:
            JSON string with the new fulfillment's ID.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_fulfillment",
                }
            )
        fulfillment = {"orderId": order_id, "lineItemsByIds": line_items}
        if tracking_number:
            fulfillment["trackingInfo"] = {"number": tracking_number}
            if tracking_company:
                fulfillment["trackingInfo"]["company"] = tracking_company
        graphql_mutation = """
        mutation fulfillmentCreateV2($fulfillment: FulfillmentV2Input!) {
          fulfillmentCreateV2(fulfillment: $fulfillment) {
            fulfillment {
              id
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
            "fulfillmentCreateV2",
            graphql_mutation,
            variables={"fulfillment": fulfillment},
        )

    async def update_fulfillment_tracking(
        self, fulfillment_id: str, tracking_number: str, tracking_company: str
    ) -> str:
        """
        [Fulfillment] - Update tracking information for a fulfillment.

        Description: Adds or updates the tracking number and carrier for a shipment.

        Required Permissions: write_fulfillments

        Example Usage:
        - "Update tracking for fulfillment 'gid://.../Fulfillment/789' to 12345 with carrier 'FedEx'." -> update_fulfillment_tracking(fulfillment_id="gid://.../Fulfillment/789", tracking_number="12345", tracking_company="FedEx")

        Args:
            fulfillment_id (str): The GraphQL ID of the fulfillment.
            tracking_number (str): The new tracking number.
            tracking_company (str): The new shipping carrier.

        Returns:
            JSON string with the updated fulfillment details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_fulfillment_tracking",
                }
            )
        input_vars = {
            "fulfillmentId": fulfillment_id,
            "trackingInfo": {"number": tracking_number, "company": tracking_company},
        }
        graphql_mutation = """
        mutation fulfillmentTrackingInfoUpdateV2($fulfillmentId: ID!, $trackingInfo: FulfillmentTrackingInfoInput!) {
          fulfillmentTrackingInfoUpdateV2(fulfillmentId: $fulfillmentId, trackingInfo: $trackingInfo) {
            fulfillment {
              id
              trackingInfo {
                number
                company
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "fulfillmentTrackingInfoUpdateV2", graphql_mutation, variables=input_vars
        )

    async def create_refund(
        self, order_id: str, amount: str, currency: str, note: Optional[str] = None
    ) -> str:
        """
        [Refunds] - Issue a refund for an order.

        Description: Creates a refund for a specified amount. This can be a partial or full refund.

        Required Permissions: write_orders

        Example Usage:
        - "Refund $10.00 on order 'gid://.../123'." -> create_refund(order_id="gid://.../123", amount="10.00", currency="USD")

        Args:
            order_id (str): The GraphQL ID of the order.
            amount (str): The amount to refund.
            currency (str): The currency code (e.g., 'USD').
            note (Optional[str]): A note explaining the refund.

        Returns:
            JSON string with the created refund's details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_refund",
                }
            )
        input_vars = {
            "orderId": order_id,
            "note": note,
            "transactions": [
                {
                    "gateway": "manual",
                    "amount": amount,
                    "kind": "REFUND",
                    "orderId": order_id,
                }
            ],
        }
        graphql_mutation = """
        mutation refundCreate($input: RefundInput!) {
          refundCreate(input: $input) {
            refund {
              id
              createdAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "refundCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_draft_orders(self, limit: int = 10) -> str:
        """
        [Draft Orders] - Retrieve a list of draft orders.

        Required Permissions: read_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f"{{ draftOrders(first: {limit}) {{ edges {{ node {{ id name status }} }} }} }}"
        return self._execute_query("get_draft_orders", graphql_query)

    async def get_draft_order_by_id(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Retrieve a specific draft order by its ID.

        Required Permissions: read_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ draftOrder(id: "{draft_order_id}") {{ id name lineItems(first: 5) {{ edges {{ node {{ title quantity }} }} }} }} }}'
        return self._execute_query("get_draft_order_by_id", graphql_query)

    async def create_draft_order(
        self, line_items: list[dict], note: Optional[str] = None
    ) -> str:
        """
        [Draft Orders] - Create a new draft order.

        Required Permissions: write_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {"lineItems": line_items, "note": note}
        graphql_mutation = """
        mutation draftOrderCreate($input: DraftOrderInput!) {
          draftOrderCreate(input: $input) {
            draftOrder { id name }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "draftOrderCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_draft_order(self, draft_order_id: str, **kwargs) -> str:
        """
        [Draft Orders] - Update an existing draft order.

        Required Permissions: write_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {**kwargs, "id": draft_order_id}
        graphql_mutation = """
        mutation draftOrderUpdate($id: ID!, $input: DraftOrderInput!) {
          draftOrderUpdate(id: $id, input: $input) {
            draftOrder { id name }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "draftOrderUpdate",
            graphql_mutation,
            variables={"id": draft_order_id, "input": kwargs},
        )

    async def complete_draft_order(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Complete a draft order, creating a real order.

        Required Permissions: write_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation draftOrderComplete($id: ID!) {
          draftOrderComplete(id: $id) {
            order { id name }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "draftOrderComplete", graphql_mutation, variables={"id": draft_order_id}
        )

    async def send_draft_order_invoice(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Send an invoice for a draft order.

        Required Permissions: write_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation draftOrderInvoiceSend($id: ID!) {
          draftOrderInvoiceSend(id: $id) {
            draftOrder { id status }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "draftOrderInvoiceSend", graphql_mutation, variables={"id": draft_order_id}
        )

    async def delete_draft_order(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Delete a draft order.

        Required Permissions: write_draft_orders
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation draftOrderDelete($id: ID!) {
          draftOrderDelete(id: $id) {
            deletedId
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "draftOrderDelete", graphql_mutation, variables={"id": draft_order_id}
        )

    async def create_basic_discount_code(self, code: str, percentage: float) -> str:
        """
        [Promotions] - Create a basic percentage-based discount code.

        Required Permissions: write_discounts
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {
            "basicCodeDiscount": {
                "title": code,
                "code": code,
                "customerSelection": {"allCustomers": True},
                "startsAt": "2022-01-01T00:00:00Z",
                "appliesOncePerCustomer": True,
                "value": {"percentageValue": percentage},
            }
        }
        graphql_mutation = """
        mutation discountCodeBasicCreate($basicCodeDiscount: DiscountCodeBasicInput!) {
            discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
                codeDiscountNode { id }
                userErrors { field message }
            }
        }
        """
        return self._execute_query(
            "discountCodeBasicCreate", graphql_mutation, variables=input_vars
        )

    async def get_discount_codes(self, limit: int = 10) -> str:
        """
        [Promotions] - Get a list of discount codes.

        Required Permissions: read_discounts
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f"{{ codeDiscountNodes(first: {limit}) {{ edges {{ node {{ id ... on DiscountCodeBasic {{ title }} }} }} }} }}"
        return self._execute_query("get_discount_codes", graphql_query)

    async def update_basic_discount_code(self, discount_id: str, **kwargs) -> str:
        """
        [Promotions] - Update a basic discount code.

        Required Permissions: write_discounts
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation discountCodeBasicUpdate($id: ID!, $basicCodeDiscount: DiscountCodeBasicInput!) {
            discountCodeBasicUpdate(id: $id, basicCodeDiscount: $basicCodeDiscount) {
                codeDiscountNode { id }
                userErrors { field message }
            }
        }
        """
        return self._execute_query(
            "discountCodeBasicUpdate",
            graphql_mutation,
            variables={"id": discount_id, "basicCodeDiscount": kwargs},
        )

    async def delete_discount_code(self, discount_id: str) -> str:
        """
        [Promotions] - Delete a discount code.

        Required Permissions: write_discounts
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation discountCodeDelete($id: ID!) {
            discountCodeDelete(id: $id) {
                deletedId
                userErrors { field message }
            }
        }
        """
        return self._execute_query(
            "discountCodeDelete", graphql_mutation, variables={"id": discount_id}
        )

    async def create_gift_card(
        self, initial_value: float, note: Optional[str] = None
    ) -> str:
        """
        [Promotions] - Create a new gift card.

        Required Permissions: write_gift_cards
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {"initialValue": initial_value, "note": note}
        graphql_mutation = """
        mutation giftCardCreate($input: GiftCardCreateInput!) {
          giftCardCreate(input: $input) {
            giftCard { id lastCharacters }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "giftCardCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_locations(self, limit: int = 10) -> str:
        """
        [Locations] - Retrieve a list of store locations.

        Required Permissions: read_locations
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f"{{ locations(first: {limit}) {{ edges {{ node {{ id name isActive }} }} }} }}"
        return self._execute_query("get_locations", graphql_query)

    async def get_location_by_id(self, location_id: str) -> str:
        """
        [Locations] - Retrieve a specific location by its ID.

        Required Permissions: read_locations
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ location(id: "{location_id}") {{ id name address {{ address1 city }} }} }}'
        return self._execute_query("get_location_by_id", graphql_query)

    async def activate_location(self, location_id: str) -> str:
        """
        [Locations] - Activate a deactivated location.

        Required Permissions: write_locations
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation locationActivate($id: ID!) {
          locationActivate(id: $id) {
            location { id isActive }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "locationActivate", graphql_mutation, variables={"id": location_id}
        )

    async def deactivate_location(self, location_id: str) -> str:
        """
        [Locations] - Deactivate an active location.

        Required Permissions: write_locations
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation locationDeactivate($id: ID!) {
          locationDeactivate(id: $id) {
            location { id isActive }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "locationDeactivate", graphql_mutation, variables={"id": location_id}
        )

    async def get_returns(self, limit: int = 10) -> str:
        """
        [Returns] - Retrieve a list of returns.

        Required Permissions: read_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = (
            f"{{ returns(first: {limit}) {{ edges {{ node {{ id name status }} }} }} }}"
        )
        return self._execute_query("get_returns", graphql_query)

    async def get_return_by_id(self, return_id: str) -> str:
        """
        [Returns] - Retrieve a specific return by its ID.

        Required Permissions: read_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ return(id: "{return_id}") {{ id name returnLineItems(first: 5) {{ edges {{ node {{ id }} }} }} }} }}'
        return self._execute_query("get_return_by_id", graphql_query)

    async def create_return(self, order_id: str, line_items: list[dict]) -> str:
        """
        [Returns] - Create a return for an order.

        Required Permissions: write_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {
            "returnInput": {"orderId": order_id, "returnLineItems": line_items}
        }
        graphql_mutation = """
        mutation returnRequest($returnInput: ReturnInput!) {
          returnRequest(returnInput: $returnInput) {
            return { id status }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "returnRequest", graphql_mutation, variables=input_vars
        )

    async def approve_return(self, return_id: str) -> str:
        """
        [Returns] - Approve a pending return request.

        Required Permissions: write_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation returnApprove($id: ID!) {
          returnApprove(id: $id) {
            return { id status }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "returnApprove", graphql_mutation, variables={"id": return_id}
        )

    async def decline_return(self, return_id: str, reason: str) -> str:
        """
        [Returns] - Decline a pending return request.

        Required Permissions: write_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation returnDecline($id: ID!, $reason: String!) {
          returnDecline(id: $id, reason: $reason) {
            return { id status }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "returnDecline",
            graphql_mutation,
            variables={"id": return_id, "reason": reason},
        )

    async def close_return(self, return_id: str) -> str:
        """
        [Returns] - Close an open return.

        Required Permissions: write_returns
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation returnClose($id: ID!) {
          returnClose(id: $id) {
            return { id status }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "returnClose", graphql_mutation, variables={"id": return_id}
        )

    async def create_staged_upload(self, input: dict) -> str:
        """
        [Files] - Create a staged upload target for a file.

        Required Permissions: write_files
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
          stagedUploadsCreate(input: $input) {
            stagedTargets { url parameters { name value } }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "stagedUploadsCreate", graphql_mutation, variables={"input": [input]}
        )

    async def get_files(self, limit: int = 10, query: Optional[str] = None) -> str:
        """
        [Files] - Retrieve a list of files from the store.

        Required Permissions: read_files
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        q = f', query: "{query}"' if query else ""
        graphql_query = f"{{ files(first: {limit}{q}) {{ edges {{ node {{ ... on MediaImage {{ id image {{ url }} }} }} }} }} }}"
        return self._execute_query("get_files", graphql_query)

    async def file_create(self, files: list[dict]) -> str:
        """
        [Files] - Create new files from staged uploads.

        Required Permissions: write_files
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation fileCreate($files: [FileCreateInput!]!) {
          fileCreate(files: $files) {
            files { id ... on MediaImage { image { url } } }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "fileCreate", graphql_mutation, variables={"files": files}
        )

    async def delete_files(self, file_ids: list[str]) -> str:
        """
        [Files] - Delete files from the store.

        Required Permissions: write_files
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation fileDelete($fileIds: [ID!]!) {
          fileDelete(fileIds: $fileIds) {
            deletedFileIds
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "fileDelete", graphql_mutation, variables={"fileIds": file_ids}
        )

    async def get_reports(self, limit: int = 10) -> str:
        """
        [Reports] - Retrieve a list of reports.

        Required Permissions: read_reports
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f"{{ reports(first: {limit}) {{ edges {{ node {{ id title shopifyQl }} }} }} }}"
        return self._execute_query("get_reports", graphql_query)

    async def get_report_by_id(self, report_id: str) -> str:
        """
        [Reports] - Retrieve a specific report by its ID.

        Required Permissions: read_reports
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ report(id: "{report_id}") {{ id title shopifyQl }} }}'
        return self._execute_query("get_report_by_id", graphql_query)

    async def get_blogs(self, limit: int = 10) -> str:
        """
        [Content] - Get a list of blogs.

        Required Permissions: read_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = (
            f"{{ blogs(first: {limit}) {{ edges {{ node {{ id title handle }} }} }} }}"
        )
        return self._execute_query("get_blogs", graphql_query)

    async def get_articles(self, blog_id: str, limit: int = 10) -> str:
        """
        [Content] - Get articles from a specific blog.

        Required Permissions: read_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ blog(id: "{blog_id}") {{ articles(first: {limit}) {{ edges {{ node {{ id title }} }} }} }} }}'
        return self._execute_query("get_articles", graphql_query)

    async def get_article_by_id(self, article_id: str) -> str:
        """
        [Content] - Get a specific article by its ID.

        Required Permissions: read_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ article(id: "{article_id}") {{ id title contentHtml }} }}'
        return self._execute_query("get_article_by_id", graphql_query)

    async def create_article(self, blog_id: str, title: str, content_html: str) -> str:
        """
        [Content] - Create a new article in a blog.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {"blogId": blog_id, "title": title, "contentHtml": content_html}
        graphql_mutation = """
        mutation articleCreate($blogId: ID!, $input: ArticleInput!) {
          articleCreate(blogId: $blogId, input: $input) {
            article { id title }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "articleCreate",
            graphql_mutation,
            variables={
                "blogId": blog_id,
                "input": {"title": title, "contentHtml": content_html},
            },
        )

    async def update_article(self, article_id: str, **kwargs) -> str:
        """
        [Content] - Update an existing article.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation articleUpdate($id: ID!, $input: ArticleInput!) {
          articleUpdate(id: $id, input: $input) {
            article { id title }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "articleUpdate",
            graphql_mutation,
            variables={"id": article_id, "input": kwargs},
        )

    async def delete_article(self, article_id: str) -> str:
        """
        [Content] - Delete an article.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation articleDelete($id: ID!) {
          articleDelete(id: $id) {
            deletedId
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "articleDelete", graphql_mutation, variables={"id": article_id}
        )

    async def get_pages(self, limit: int = 10) -> str:
        """
        [Content] - Get a list of pages.

        Required Permissions: read_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = (
            f"{{ pages(first: {limit}) {{ edges {{ node {{ id title }} }} }} }}"
        )
        return self._execute_query("get_pages", graphql_query)

    async def get_page_by_id(self, page_id: str) -> str:
        """
        [Content] - Get a specific page by its ID.

        Required Permissions: read_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ page(id: "{page_id}") {{ id title body }} }}'
        return self._execute_query("get_page_by_id", graphql_query)

    async def create_page(self, title: str, body_html: str) -> str:
        """
        [Content] - Create a new page.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {"title": title, "bodyHtml": body_html}
        graphql_mutation = """
        mutation pageCreate($input: PageInput!) {
          pageCreate(input: $input) {
            page { id title }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "pageCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_page(self, page_id: str, **kwargs) -> str:
        """
        [Content] - Update an existing page.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation pageUpdate($input: PageInput!) {
          pageUpdate(input: $input) {
            page { id title }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "pageUpdate",
            graphql_mutation,
            variables={"input": {**kwargs, "id": page_id}},
        )

    async def delete_page(self, page_id: str) -> str:
        """
        [Content] - Delete a page.

        Required Permissions: write_content
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation pageDelete($id: ID!) {
          pageDelete(id: $id) {
            deletedPageId
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "pageDelete", graphql_mutation, variables={"id": page_id}
        )

    async def get_marketing_events(self, limit: int = 10) -> str:
        """
        [Marketing] - Retrieve a list of marketing events.

        Required Permissions: read_marketing
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f"{{ marketingEvents(first: {limit}) {{ edges {{ node {{ id appTitle description }} }} }} }}"
        return self._execute_query("get_marketing_events", graphql_query)

    async def get_marketing_event_by_id(self, event_id: str) -> str:
        """
        [Marketing] - Retrieve a specific marketing event by its ID.

        Required Permissions: read_marketing
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = f'{{ marketingEvent(id: "{event_id}") {{ id description }} }}'
        return self._execute_query("get_marketing_event_by_id", graphql_query)

    async def create_marketing_event(self, input: dict) -> str:
        """
        [Marketing] - Create a new marketing event.

        Required Permissions: write_marketing
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation marketingEventCreate($marketingEvent: MarketingEventInput!) {
          marketingEventCreate(marketingEvent: $marketingEvent) {
            marketingEvent { id }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "marketingEventCreate",
            graphql_mutation,
            variables={"marketingEvent": input},
        )

    async def update_marketing_event(self, event_id: str, input: dict) -> str:
        """
        [Marketing] - Update an existing marketing event.

        Required Permissions: write_marketing
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation marketingEventUpdate($id: ID!, $marketingEvent: MarketingEventInput!) {
          marketingEventUpdate(id: $id, marketingEvent: $marketingEvent) {
            marketingEvent { id }
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "marketingEventUpdate",
            graphql_mutation,
            variables={"id": event_id, "marketingEvent": input},
        )

    async def delete_marketing_event(self, event_id: str) -> str:
        """
        [Marketing] - Delete a marketing event.

        Required Permissions: write_marketing
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_mutation = """
        mutation marketingEventDelete($id: ID!) {
          marketingEventDelete(id: $id) {
            deletedId
            userErrors { field message }
          }
        }
        """
        return self._execute_query(
            "marketingEventDelete", graphql_mutation, variables={"id": event_id}
        )

    async def get_shipping_zones(self, limit: int = 10) -> str:
        """
        [Shipping] - Retrieve a list of shipping zones.

        Required Permissions: read_shipping
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = (
            f"{{ shippingZones(first: {limit}) {{ edges {{ node {{ id name }} }} }} }}"
        )
        return self._execute_query("get_shipping_zones", graphql_query)

    async def get_shipping_zone_by_id(self, zone_id: str) -> str:
        """
        [Shipping] - Retrieve a specific shipping zone by its ID.

        Required Permissions: read_shipping
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        graphql_query = (
            f'{{ shippingZone(id: "{zone_id}") {{ id name countries {{ name }} }} }}'
        )
        return self._execute_query("get_shipping_zone_by_id", graphql_query)

    async def create_shipping_zone(self, name: str, country_codes: list[str]) -> str:
        """
        [Shipping] - Create a new shipping zone.

        Required Permissions: write_shipping
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        input_vars = {"name": name, "countries": country_codes}
        try:
            new_zone = shopify.ShippingZone.create(input_vars)
            return json.dumps({"success": True, "data": new_zone.to_dict()})
        except Exception as e:
            logging.exception(f"Error in create_shipping_zone: {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def update_shipping_zone(self, zone_id: str, **kwargs) -> str:
        """
        [Shipping] - Update an existing shipping zone.

        Required Permissions: write_shipping
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        try:
            zone = shopify.ShippingZone.find(zone_id)
            for key, value in kwargs.items():
                setattr(zone, key, value)
            zone.save()
            return json.dumps({"success": True, "data": zone.to_dict()})
        except Exception as e:
            logging.exception(f"Error in update_shipping_zone: {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def delete_shipping_zone(self, zone_id: str) -> str:
        """
        [Shipping] - Delete a shipping zone.

        Required Permissions: write_shipping
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {"success": False, "error": "Shopify session not available."}
            )
        try:
            shopify.ShippingZone.delete(zone_id)
            return json.dumps({"success": True, "deleted_id": zone_id})
        except Exception as e:
            logging.exception(f"Error in delete_shipping_zone: {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def get_shipping_rates(self, zone_id: str) -> str:
        """
        [Shipping] - Get shipping rates for a zone.

        Required Permissions: read_shipping
        """
        return await self.get_shipping_zone_by_id(zone_id)

    async def create_shipping_rate(self, zone_id: str, name: str, price: str) -> str:
        """
        [Shipping] - Create a new shipping rate for a zone.

        Required Permissions: write_shipping
        """
        return json.dumps(
            {
                "success": False,
                "error": "Complex: Use update_shipping_zone with rate data.",
            }
        )

    async def update_shipping_rate(self, zone_id: str, rate_id: str, **kwargs) -> str:
        """
        [Shipping] - Update an existing shipping rate.

        Required Permissions: write_shipping
        """
        return json.dumps(
            {
                "success": False,
                "error": "Complex: Use update_shipping_zone with rate data.",
            }
        )

    async def delete_shipping_rate(self, zone_id: str, rate_id: str) -> str:
        """
        [Shipping] - Delete a shipping rate from a zone.

        Required Permissions: write_shipping
        """
        return json.dumps(
            {
                "success": False,
                "error": "Complex: Use update_shipping_zone to remove rate data.",
            }
        )

    async def get_shop_policies(self) -> str:
        """
        [Legal Policies] - Retrieve all shop policies.

        Description: Fetches the content of all configured shop policies, including privacy, refund, shipping, and terms of service.

        Required Permissions: read_policies

        Example Usage:
        - "Show me all the shop policies." -> get_shop_policies()

        Returns:
            JSON string with the body content and type for each policy.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_shop_policies",
                }
            )
        graphql_query = """
        {
          shop {
            shopPolicies {
              type
              body
            }
          }
        }
        """
        return self._execute_query("get_shop_policies", graphql_query)

    async def update_shop_policy(self, policy_type: str, body: str) -> str:
        """
        [Legal Policies] - Update a specific shop policy.

        Description: A helper function to update various shop policies. Use specialized functions like `update_privacy_policy` where available.

        Required Permissions: write_policies

        Example Usage:
        - "Update the privacy policy." -> update_shop_policy(policy_type="PRIVACY_POLICY", body="New privacy content.")

        Args:
            policy_type (str): The type of policy to update (e.g., 'PRIVACY_POLICY').
            body (str): The new HTML content for the policy.

        Returns:
            JSON string with the updated policy details or an error message.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_shop_policy",
                }
            )
        input_vars = {"shopPolicy": {"type": policy_type, "body": body}}
        graphql_mutation = """
        mutation shopPolicyUpdate($shopPolicy: ShopPolicyInput!) {
          shopPolicyUpdate(shopPolicy: $shopPolicy) {
            shopPolicy {
              body
              type
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "shopPolicyUpdate", graphql_mutation, variables=input_vars
        )

    async def update_privacy_policy(self, body: str) -> str:
        """[Legal Policies] - Update the privacy policy. Alias for update_shop_policy."""
        return await self.update_shop_policy("PRIVACY_POLICY", body)

    async def update_terms_of_service(self, body: str) -> str:
        """[Legal Policies] - Update the terms of service. Alias for update_shop_policy."""
        return await self.update_shop_policy("TERMS_OF_SERVICE", body)

    async def update_refund_policy(self, body: str) -> str:
        """[Legal Policies] - Update the refund policy. Alias for update_shop_policy."""
        return await self.update_shop_policy("REFUND_POLICY", body)

    async def update_shipping_policy(self, body: str) -> str:
        """[Legal Policies] - Update the shipping policy. Alias for update_shop_policy."""
        return await self.update_shop_policy("SHIPPING_POLICY", body)

    async def get_markets(self, limit: int = 10) -> str:
        """
        [Markets] - Retrieve a list of configured markets.

        Description: Fetches markets, including their regions and currency settings.

        Required Permissions: read_markets

        Example Usage:
        - "List all active markets." -> get_markets()

        Args:
            limit (int): Max number of markets to return.

        Returns:
            JSON string with a list of markets.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_markets",
                }
            )
        graphql_query = f"\n        {{\n          markets(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                name\n                enabled\n                regions {{\n                  name\n                  code\n                }}\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_markets", graphql_query)

    async def get_market_by_id(self, market_id: str) -> str:
        """
        [Markets] - Get a specific market by its GraphQL ID.

        Description: Retrieves detailed information for a single market.

        Required Permissions: read_markets

        Example Usage:
        - "Show details for market 'gid://shopify/Market/123'." -> get_market_by_id(market_id="gid://shopify/Market/123")

        Args:
            market_id (str): The GraphQL ID of the market.

        Returns:
            JSON string with market details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_market_by_id",
                }
            )
        graphql_query = f'\n        {{\n          market(id: "{market_id}") {{\n            id\n            name\n            enabled\n            currencySettings {{\n              baseCurrency {{\n                currencyCode\n              }}\n            }}\n            regions {{\n              ... on MarketRegionCountry {{\n                name\n                code\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_market_by_id", graphql_query)

    async def create_market(self, name: str, regions: list[str]) -> str:
        """
        [Markets] - Create a new market.

        Description: Creates a new market with specified regions.

        Required Permissions: write_markets

        Example Usage:
        - "Create a 'North America' market for US and CA." -> create_market(name="North America", regions=["US", "CA"])

        Args:
            name (str): The name of the market.
            regions (list[str]): List of country codes (e.g., ["US", "CA"]).

        Returns:
            JSON string with the new market's ID.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "create_market",
                }
            )
        input_vars = {"name": name, "regions": {"add": regions}}
        graphql_mutation = """
        mutation marketCreate($input: MarketCreateInput!) {
          marketCreate(input: $input) {
            market {
              id
              name
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "marketCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_market(self, market_id: str, **kwargs) -> str:
        """
        [Markets] - Update an existing market.

        Description: Modifies properties of a market like its name or regions.

        Required Permissions: write_markets

        Example Usage:
        - "Rename market 'gid://.../123' to 'European Union'." -> update_market(market_id="gid://.../123", name="European Union")

        Args:
            market_id (str): The GraphQL ID of the market.
            **kwargs: Fields to update (e.g., name, regions_add, regions_remove).

        Returns:
            JSON string with updated market data.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "update_market",
                }
            )
        input_vars = {"id": market_id}
        if "name" in kwargs:
            input_vars["name"] = kwargs["name"]
        if "regions_add" in kwargs or "regions_remove" in kwargs:
            input_vars["regions"] = {
                "add": kwargs.get("regions_add", []),
                "remove": kwargs.get("regions_remove", []),
            }
        graphql_mutation = """
        mutation marketUpdate($input: MarketUpdateInput!) {
          marketUpdate(input: $input) {
            market {
              id
              name
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "marketUpdate", graphql_mutation, variables={"input": input_vars}
        )

    async def delete_market(self, market_id: str) -> str:
        """
        [Markets] - Delete a market.

        Description: Permanently removes a market.

        Required Permissions: write_markets

        Example Usage:
        - "Delete market 'gid://.../123'." -> delete_market(market_id="gid://.../123")

        Args:
            market_id (str): The GraphQL ID of the market to delete.

        Returns:
            JSON string with the ID of the deleted market.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "delete_market",
                }
            )
        graphql_mutation = """
        mutation marketDelete($id: ID!) {
          marketDelete(id: $id) {
            deletedId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "marketDelete", graphql_mutation, variables={"id": market_id}
        )

    async def get_market_catalogs(self, market_id: str) -> str:
        """
        [Markets] - Get product catalogs for a market.

        Description: Retrieves the list of product catalogs associated with a specific market.

        Required Permissions: read_markets

        Example Usage:
        - "Show catalogs for market 'gid://.../123'." -> get_market_catalogs(market_id="gid://.../123")

        Args:
            market_id (str): The GraphQL ID of the market.

        Returns:
            JSON string with catalog details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_market_catalogs",
                }
            )
        graphql_query = f'\n        {{\n          market(id: "{market_id}") {{\n            catalogs(first: 5) {{\n              edges {{\n                node {{\n                  id\n                  title\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_market_catalogs", graphql_query)

    async def get_themes(self, limit: int = 10) -> str:
        """
        [Themes] - Retrieve a list of themes in the theme library.

        Description: Fetches themes, including their roles (e.g., MAIN, UNPUBLISHED).

        Required Permissions: read_themes

        Example Usage:
        - "List all themes in the store." -> get_themes()

        Args:
            limit (int): Max number of themes to return.

        Returns:
            JSON string with a list of themes.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_themes",
                }
            )
        graphql_query = f"\n        {{\n          themes(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                name\n                role\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_themes", graphql_query)

    async def get_theme_by_id(self, theme_id: str) -> str:
        """
        [Themes] - Get a specific theme by its GraphQL ID.

        Description: Retrieves detailed information for a single theme.

        Required Permissions: read_themes

        Example Usage:
        - "Show details for theme 'gid://.../Theme/123'." -> get_theme_by_id(theme_id="gid://.../Theme/123")

        Args:
            theme_id (str): The GraphQL ID of the theme.

        Returns:
            JSON string with theme details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_theme_by_id",
                }
            )
        graphql_query = f'\n        {{\n          node(id: "{theme_id}") {{\n            ... on Theme {{\n              id\n              name\n              role\n              createdAt\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_theme_by_id", graphql_query)

    async def get_theme_assets(self, theme_id: str, limit: int = 250) -> str:
        """
        [Themes] - Get assets for a specific theme.

        Description: Retrieves a list of asset files (templates, layouts, snippets, etc.) for a theme.

        Required Permissions: read_themes

        Example Usage:
        - "List all assets for theme 'gid://.../Theme/123'." -> get_theme_assets(theme_id="gid://.../Theme/123")

        Args:
            theme_id (str): The GraphQL ID of the theme.
            limit (int): The max number of assets to return.

        Returns:
            JSON string with a list of assets.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_theme_assets",
                }
            )
        try:
            theme = shopify.Theme.find(theme_id.split("/")[-1])
            assets = shopify.Asset.find(theme_id=theme.id)
            asset_list = [
                {"key": asset.key, "public_url": asset.public_url} for asset in assets
            ]
            return json.dumps(
                {"success": True, "data": asset_list, "tool": "get_theme_assets"}
            )
        except Exception as e:
            logging.exception(f"Error in get_theme_assets: {e}")
            return json.dumps(
                {"success": False, "error": str(e), "tool": "get_theme_assets"}
            )

    async def get_theme_asset(self, theme_id: str, key: str) -> str:
        """
        [Themes] - Get a specific theme asset by key.

        Description: Retrieves the content of a single theme asset file.

        Required Permissions: read_themes

        Example Usage:
        - "Get the content of 'templates/product.liquid' for theme 'gid://.../Theme/123'." -> get_theme_asset(theme_id="gid://.../Theme/123", key="templates/product.liquid")

        Args:
            theme_id (str): The GraphQL ID of the theme.
            key (str): The key of the asset (e.g., "templates/product.liquid").

        Returns:
            JSON string with the asset's content.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_theme_asset",
                }
            )
        try:
            theme_numeric_id = theme_id.split("/")[-1]
            asset = shopify.Asset.find(theme_id=theme_numeric_id, key=key)
            return json.dumps(
                {
                    "success": True,
                    "data": {"key": asset.key, "value": asset.value},
                    "tool": "get_theme_asset",
                }
            )
        except Exception as e:
            logging.exception(f"Error in get_theme_asset: {e}")
            return json.dumps(
                {"success": False, "error": str(e), "tool": "get_theme_asset"}
            )

    async def update_theme_asset(self, theme_id: str, key: str, value: str) -> str:
        """
        [Themes] - Update a specific theme asset.

        Description: Modifies the content of a theme asset file.

        Required Permissions: write_themes

        Example Usage:
        - "Update 'assets/theme.css' for theme 'gid://.../Theme/123' with new CSS." -> update_theme_asset(theme_id="gid://.../Theme/123", key="assets/theme.css", value="body { background: #000; }")

        Args:
            theme_id (str): The GraphQL ID of the theme.
            key (str): The key of the asset.
            value (str): The new content for the asset.

        Returns:
            JSON string with the updated asset's key.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "update_theme_asset",
                }
            )
        try:
            theme_numeric_id = theme_id.split("/")[-1]
            asset = shopify.Asset.find(theme_id=theme_numeric_id, key=key)
            asset.value = value
            asset.save()
            return json.dumps(
                {
                    "success": True,
                    "data": {"key": asset.key},
                    "tool": "update_theme_asset",
                }
            )
        except Exception as e:
            logging.exception(f"Error in update_theme_asset: {e}")
            return json.dumps(
                {"success": False, "error": str(e), "tool": "update_theme_asset"}
            )

    async def delete_theme_asset(self, theme_id: str, key: str) -> str:
        """
        [Themes] - Delete a theme asset.

        Description: Permanently removes an asset file from a theme.

        Required Permissions: write_themes

        Example Usage:
        - "Delete 'assets/old-style.css' from theme 'gid://.../Theme/123'." -> delete_theme_asset(theme_id="gid://.../Theme/123", key="assets/old-style.css")

        Args:
            theme_id (str): The GraphQL ID of the theme.
            key (str): The key of the asset to delete.

        Returns:
            JSON string confirming deletion.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "delete_theme_asset",
                }
            )
        try:
            theme_numeric_id = theme_id.split("/")[-1]
            asset = shopify.Asset.find(theme_id=theme_numeric_id, key=key)
            asset.destroy()
            return json.dumps(
                {
                    "success": True,
                    "data": {"deleted_key": key},
                    "tool": "delete_theme_asset",
                }
            )
        except Exception as e:
            logging.exception(f"Error in delete_theme_asset: {e}")
            return json.dumps(
                {"success": False, "error": str(e), "tool": "delete_theme_asset"}
            )

    async def get_translations(
        self, resource_id: str, locale: str, limit: int = 10
    ) -> str:
        """
        [Translations] - Get translations for a specific resource.

        Description: Fetches translations for a product, collection, etc., in a given locale.

        Required Permissions: read_translations

        Example Usage:
        - "Show French translations for product 'gid://.../Product/123'." -> get_translations(resource_id="gid://.../Product/123", locale="fr")

        Args:
            resource_id (str): The GraphQL ID of the resource.
            locale (str): The locale code (e.g., "fr").
            limit (int): Max number of translations to return.

        Returns:
            JSON string with a list of translations.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_translations",
                }
            )
        graphql_query = f'\n        {{\n          translations(resourceId: "{resource_id}", locale: "{locale}", first: {limit}) {{\n            edges {{\n              node {{\n                key\n                value\n                locale\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_translations", graphql_query)

    async def create_translation(
        self, resource_id: str, locale: str, key: str, value: str
    ) -> str:
        """
        [Translations] - Create a translation for a resource.

        Description: Adds a new translation for a specific field of a resource.

        Required Permissions: write_translations

        Example Usage:
        - "Translate the title of product 'gid://.../Product/123' to 'T-shirt' in French." -> create_translation(resource_id="gid://.../Product/123", locale="fr", key="title", value="T-shirt")

        Args:
            resource_id (str): The GraphQL ID of the resource.
            locale (str): The locale code.
            key (str): The field to translate (e.g., "title").
            value (str): The translated content.

        Returns:
            JSON string with the new translation's details.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "create_translation",
                }
            )
        input_vars = {
            "resourceId": resource_id,
            "translations": [{"locale": locale, "key": key, "value": value}],
        }
        graphql_mutation = """
        mutation translate($resourceId: ID!, $translations: [TranslationInput!]!) {
          translationsRegister(resourceId: $resourceId, translations: $translations) {
            translations {
              key
              value
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "translationsRegister", graphql_mutation, variables=input_vars
        )

    async def update_translation(
        self, resource_id: str, locale: str, key: str, value: str
    ) -> str:
        """
        [Translations] - Update a translation. Alias for create_translation, as it overwrites existing values.
        """
        return await self.create_translation(resource_id, locale, key, value)

    async def delete_translation(
        self, resource_id: str, locale: str, keys: list[str]
    ) -> str:
        """
        [Translations] - Delete translations for a resource.

        Description: Removes specific translations for a resource in a given locale.

        Required Permissions: write_translations

        Example Usage:
        - "Delete the French title translation for product 'gid://.../Product/123'." -> delete_translation(resource_id="gid://.../Product/123", locale="fr", keys=["title"])

        Args:
            resource_id (str): The GraphQL ID of the resource.
            locale (str): The locale code.
            keys (list[str]): A list of translation keys to delete.

        Returns:
            JSON string confirming deletion.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "delete_translation",
                }
            )
        input_vars = {
            "resourceId": resource_id,
            "translationKeys": [{"locale": locale, "keys": keys}],
        }
        graphql_mutation = """
        mutation translationsRemove($resourceId: ID!, $translationKeys: [TranslationKeyRemoveInput!]!) {
            translationsRemove(resourceId: $resourceId, translationKeys: $translationKeys) {
                userErrors {
                    field
                    message
                }
            }
        }
        """
        return self._execute_query(
            "translationsRemove", graphql_mutation, variables=input_vars
        )

    async def get_locales(self) -> str:
        """
        [Translations] - Get available shop locales.

        Description: Fetches a list of all locales available for the shop, including which are published.

        Required Permissions: read_locales

        Example Usage:
        - "List all available languages for the store." -> get_locales()

        Returns:
            JSON string with a list of locales.
        """
        session = await get_shopify_session(self.store_url, self.access_token)
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available.",
                    "tool": "get_locales",
                }
            )
        graphql_query = """
        {
          shopLocales {
            locale
            name
            primary
            published
          }
        }
        """
        return self._execute_query("get_locales", graphql_query)