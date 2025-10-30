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
            self.create_product_variant,
            self.update_product_variant,
            self.delete_product_variant,
            self.get_inventory_levels,
            self.adjust_inventory_level,
            self.create_collection,
            self.add_products_to_collection,
            self.get_product_metafields,
            self.set_product_metafield,
            self.get_customers,
            self.get_customer_orders,
            self.update_customer,
            self.get_orders,
            self.get_order_by_id,
            self.update_order,
            self.create_fulfillment,
            self.update_fulfillment_tracking,
            self.cancel_order,
            self.create_refund,
            self.add_order_note,
            self.tag_order,
            self.get_fulfillment_orders,
            self.tag_customer,
            self.remove_customer_tags,
            self.get_customer_metafields,
            self.set_customer_metafield,
            self.search_orders_by_customer_email,
            self.create_basic_discount_code,
            self.get_discount_codes,
            self.update_basic_discount_code,
            self.delete_discount_code,
            self.create_gift_card,
            self.get_draft_orders,
            self.get_draft_order_by_id,
            self.create_draft_order,
            self.update_draft_order,
            self.complete_draft_order,
            self.send_draft_order_invoice,
            self.delete_draft_order,
            self.get_locations,
            self.get_location_by_id,
            self.activate_location,
            self.deactivate_location,
            self.get_returns,
            self.get_return_by_id,
            self.create_return,
            self.approve_return,
            self.decline_return,
            self.close_return,
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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
        session = await get_shopify_session()
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

    async def remove_customer_tags(self, customer_id: str, tags: str) -> str:
        """
        [Customer Management] - Remove tags from a customer.

        Description: Removes one or more tags from a customer profile.

        Required Permissions: write_customers

        Example Usage:
        - "Remove the 'prospect' tag from customer 'gid://.../Customer/123'." -> remove_customer_tags(customer_id='gid://.../123', tags='prospect')

        Args:
            customer_id (str): The GraphQL ID of the customer.
            tags (str): A comma-separated string of tags to remove.

        Returns:
            JSON string confirming the tags were removed or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "remove_customer_tags",
                }
            )
        graphql_mutation = """
        mutation tagsRemove($id: ID!, $tags: [String!]!) {
          tagsRemove(id: $id, tags: $tags) {
            node {
              ... on Customer {
                id
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": customer_id, "tags": [t.strip() for t in tags.split(",")]}
        return self._execute_query("tagsRemove", graphql_mutation, variables=variables)

    async def tag_customer(self, customer_id: str, tags: str) -> str:
        """
        [Customer Management] - Add tags to a customer.

        Description: Appends one or more tags to a customer for classification and segmentation.

        Required Permissions: write_customers

        Example Usage:
        - "Tag customer 'gid://.../Customer/123' with 'VIP' and 'newsletter_subscriber'." -> tag_customer(customer_id='gid://.../123', tags='VIP, newsletter_subscriber')

        Args:
            customer_id (str): The GraphQL ID of the customer.
            tags (str): A comma-separated string of tags to add.

        Returns:
            JSON string confirming the tags were added or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "tag_customer",
                }
            )
        graphql_mutation = """
        mutation tagsAdd($id: ID!, $tags: [String!]!) {
          tagsAdd(id: $id, tags: $tags) {
            node {
              ... on Customer {
                id
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": customer_id, "tags": [t.strip() for t in tags.split(",")]}
        return self._execute_query("tagsAdd", graphql_mutation, variables=variables)

    async def get_customer_metafields(self, customer_id: str, namespace: str) -> str:
        """
        [Customer Management] - Retrieve metafields for a specific customer.

        Description: Fetches custom data attached to a customer within a given namespace.

        Required Permissions: read_customers

        Example Usage:
        - "Get 'loyalty' metafields for customer 'gid://.../123'." -> get_customer_metafields(customer_id="gid://.../123", namespace="loyalty")

        Args:
            customer_id (str): The GraphQL ID of the customer.
            namespace (str): The namespace of the metafields to retrieve.

        Returns:
            JSON string with a list of metafields or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_customer_metafields",
                }
            )
        graphql_query = f'\n        {{\n          customer(id: "{customer_id}") {{\n            metafields(namespace: "{namespace}", first: 10) {{\n              edges {{\n                node {{\n                  id\n                  namespace\n                  key\n                  value\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_customer_metafields", graphql_query)

    async def set_customer_metafield(
        self,
        owner_id: str,
        namespace: str,
        key: str,
        value: str,
        type: str = "single_line_text_field",
    ) -> str:
        """
        [Customer Management] - Set a metafield for a customer.

        Description: Creates or updates a custom data field for a customer. Refer to Shopify docs for valid types.

        Required Permissions: write_customers

        Example Usage:
        - "Set a metafield for customer 'gid://.../123' with namespace 'loyalty', key 'points', and value '500'." -> set_customer_metafield(owner_id="gid://.../123", namespace="loyalty", key="points", value="500", type="number_integer")

        Args:
            owner_id (str): The GraphQL ID of the customer (the owner of the metafield).
            namespace (str): The namespace for the metafield (e.g., 'custom', 'loyalty').
            key (str): The key for the metafield (e.g., 'points', 'tier').
            value (str): The value to set for the metafield.
            type (str): The type of metafield, e.g., 'single_line_text_field', 'number_integer'.

        Returns:
            JSON string with the created/updated metafield or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "set_customer_metafield",
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

    async def search_orders_by_customer_email(self, email: str, limit: int = 10) -> str:
        """
        [Customer Management] - Search for orders using a customer's email address.

        Description: Retrieves a list of orders associated with a specific customer email.

        Required Permissions: read_orders

        Example Usage:
        - "Find all orders for 'jane@example.com'." -> search_orders_by_customer_email(email='jane@example.com')
        - "Show the last 5 orders for 'john.doe@email.com'." -> search_orders_by_customer_email(email='john.doe@email.com', limit=5)

        Args:
            email (str): The email address of the customer.
            limit (int): The maximum number of orders to return.

        Returns:
            JSON string with order data for the specified customer.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "search_orders_by_customer_email",
                }
            )
        query_filter = f"customer_email:'{email}'"
        graphql_query = f'\n        {{\n          orders(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                name\n                displayFinancialStatus\n                displayFulfillmentStatus\n                totalPriceSet {{\n                  shopMoney {{\n                    amount\n                    currencyCode\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_orders_by_customer_email", graphql_query)

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

    async def create_fulfillment(
        self, fulfillment_order_id: str, tracking_number: str, tracking_company: str
    ) -> str:
        """
        [Order Management] - Create a fulfillment for an order.

        Description: Marks order line items as fulfilled and provides tracking information.

        Required Permissions: write_fulfillments

        Example Usage:
        - "Fulfill order 'gid://.../FulfillmentOrder/1' with tracking '123' from 'UPS'." -> create_fulfillment(fulfillment_order_id='gid://.../1', tracking_number='123', tracking_company='UPS')

        Args:
            fulfillment_order_id (str): The GraphQL ID of the fulfillment order.
            tracking_number (str): The tracking number for the shipment.
            tracking_company (str): The shipping company/carrier.

        Returns:
            JSON string with the created fulfillment's data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_fulfillment",
                }
            )
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
        fulfillment_data = {
            "lineItemsByFulfillmentOrder": [
                {"fulfillmentOrderId": fulfillment_order_id}
            ],
            "trackingInfo": {"number": tracking_number, "company": tracking_company},
        }
        return self._execute_query(
            "fulfillmentCreateV2",
            graphql_mutation,
            variables={"fulfillment": fulfillment_data},
        )

    async def update_fulfillment_tracking(
        self, fulfillment_id: str, tracking_number: str, tracking_company: str
    ) -> str:
        """
        [Order Management] - Update tracking information for a fulfillment.

        Description: Updates the tracking number and company for an existing fulfillment.

        Required Permissions: write_fulfillments

        Example Usage:
        - "Update tracking for fulfillment 'gid://.../Fulfillment/1' to '456' with 'FedEx'." -> update_fulfillment_tracking(fulfillment_id='gid://.../1', tracking_number='456', tracking_company='FedEx')

        Args:
            fulfillment_id (str): The GraphQL ID of the fulfillment.
            tracking_number (str): The new tracking number.
            tracking_company (str): The new shipping company.

        Returns:
            JSON string with the updated fulfillment data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_fulfillment_tracking",
                }
            )
        graphql_mutation = """
        mutation fulfillmentTrackingInfoUpdateV2($fulfillmentId: ID!, $trackingInfo: FulfillmentTrackingInput!) {
            fulfillmentTrackingInfoUpdateV2(fulfillmentId: $fulfillmentId, trackingInfo: $trackingInfo) {
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
        variables = {
            "fulfillmentId": fulfillment_id,
            "trackingInfo": {"number": tracking_number, "company": tracking_company},
        }
        return self._execute_query(
            "fulfillmentTrackingInfoUpdateV2", graphql_mutation, variables=variables
        )

    async def cancel_order(
        self,
        order_id: str,
        reason: str,
        notify_customer: bool = True,
        restock: bool = True,
    ) -> str:
        """
        [Order Management] - Cancel an unfulfilled order.

        Description: Cancels an order, optionally refunding, restocking, and notifying the customer.

        Required Permissions: write_orders

        Example Usage:
        - "Cancel order 'gid://.../Order/123' because the customer requested it." -> cancel_order(order_id='gid://.../123', reason='CUSTOMER')

        Args:
            order_id (str): The GraphQL ID of the order to cancel.
            reason (str): The reason for cancellation (e.g., 'CUSTOMER', 'FRAUD', 'INVENTORY', 'OTHER').
            notify_customer (bool): Whether to send a cancellation email to the customer.
            restock (bool): Whether to restock the inventory for the canceled items.

        Returns:
            JSON string confirming the cancellation job or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "cancel_order",
                }
            )
        graphql_mutation = """
        mutation orderCancel($id: ID!, $reason: OrderCancelReason!, $notifyCustomer: Boolean, $restock: Boolean) {
          orderCancel(id: $id, reason: $reason, notifyCustomer: $notifyCustomer, restock: $restock) {
            order {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {
            "id": order_id,
            "reason": reason,
            "notifyCustomer": notify_customer,
            "restock": restock,
        }
        return self._execute_query("orderCancel", graphql_mutation, variables=variables)

    async def create_refund(
        self, order_id: str, line_item_id: str, quantity: int, reason: str
    ) -> str:
        """
        [Order Management] - Create a refund for an order.

        Description: Issues a full or partial refund for specific line items in an order.

        Required Permissions: write_orders

        Example Usage:
        - "Refund 1 item 'gid://.../LineItem/456' from order 'gid://.../Order/123' for 'return'." -> create_refund(order_id='gid://.../123', line_item_id='gid://.../456', quantity=1, reason='return')

        Args:
            order_id (str): The GraphQL ID of the order to refund.
            line_item_id (str): The GraphQL ID of the line item to refund.
            quantity (int): The quantity of the line item to refund.
            reason (str): The reason for the refund.

        Returns:
            JSON string with the created refund's data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_refund",
                }
            )
        graphql_mutation = """
        mutation refundCreate($input: RefundInput!) {
          refundCreate(input: $input) {
            refund {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        input_vars = {
            "orderId": order_id,
            "note": reason,
            "refundLineItems": [{"lineItemId": line_item_id, "quantity": quantity}],
        }
        return self._execute_query(
            "refundCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def add_order_note(self, order_id: str, note: str) -> str:
        """
        [Order Management] - Add a note to an order.

        Description: Appends a note to an order's timeline. This is the same as the update_order tool but more specific.

        Required Permissions: write_orders

        Example Usage:
        - "Add note 'customer called to confirm' to order 'gid://.../Order/123'." -> add_order_note(order_id='gid://.../123', note='customer called to confirm')

        Args:
            order_id (str): The GraphQL ID of the order.
            note (str): The note content to add.

        Returns:
            JSON string with the updated order data.
        """
        return await self.update_order(order_id=order_id, note=note)

    async def tag_order(self, order_id: str, tags: str) -> str:
        """
        [Order Management] - Add tags to an order.

        Description: Appends one or more tags to an order for classification.

        Required Permissions: write_orders

        Example Usage:
        - "Tag order 'gid://.../Order/123' with 'VIP' and 'priority'." -> tag_order(order_id='gid://.../123', tags='VIP, priority')

        Args:
            order_id (str): The GraphQL ID of the order.
            tags (str): A comma-separated string of tags to add.

        Returns:
            JSON string confirming the tags were added or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "tag_order",
                }
            )
        graphql_mutation = """
        mutation tagsAdd($id: ID!, $tags: [String!]!) {
          tagsAdd(id: $id, tags: $tags) {
            node {
              ... on Order {
                id
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": order_id, "tags": [t.strip() for t in tags.split(",")]}
        return self._execute_query("tagsAdd", graphql_mutation, variables=variables)

    async def get_fulfillment_orders(self, order_id: str, limit: int = 10) -> str:
        """
        [Order Management] - Get fulfillment orders for a specific order.

        Description: Retrieves a list of fulfillment orders associated with a given order, which are used to manage the fulfillment process.

        Required Permissions: read_fulfillments

        Example Usage:
        - "Get fulfillment orders for order 'gid://shopify/Order/12345'." -> get_fulfillment_orders(order_id="gid://shopify/Order/12345")

        Args:
            order_id (str): The GraphQL ID of the order.
            limit (int): The maximum number of fulfillment orders to return.

        Returns:
            JSON string with fulfillment order details, including status and line items.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_fulfillment_orders",
                }
            )
        graphql_query = f'\n        {{\n          order(id: "{order_id}") {{\n            fulfillmentOrders(first: {limit}) {{\n              edges {{\n                node {{\n                  id\n                  status\n                  requestStatus\n                  supportedActions {{\n                    action\n                  }}\n                  lineItems(first: 10) {{\n                    edges {{\n                        node {{\n                            id\n                            quantity\n                        }}\n                    }}\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_fulfillment_orders", graphql_query)

    async def create_basic_discount_code(
        self, code: str, percentage: float, applies_to_all_products: bool = True
    ) -> str:
        """
        [Pricing & Promotions] - Create a new basic discount code.

        Description: Creates a simple percentage-based discount code. For more complex discounts, use the Shopify Admin.

        Required Permissions: write_discounts

        Example Usage:
        - "Create a 10% discount code 'SAVE10' for all products." -> create_basic_discount_code(code="SAVE10", percentage=10, applies_to_all_products=True)

        Args:
            code (str): The discount code (e.g., 'SUMMER2024').
            percentage (float): The discount percentage (e.g., 10 for 10%).
            applies_to_all_products (bool): If true, the discount applies to all products.

        Returns:
            JSON string with the created discount code's data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_basic_discount_code",
                }
            )
        discount_input = {
            "code": code,
            "customerSelection": {"allCustomers": True},
            "value": {"percentageValue": percentage / 100},
            "appliesTo": {"allProducts": applies_to_all_products},
            "startsAt": "2024-01-01T00:00:00Z",
        }
        graphql_mutation = """
        mutation discountCodeBasicCreate($basicCodeDiscount: DiscountCodeBasicInput!) {
          discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
            codeDiscountNode {
              codeDiscount {
                ... on DiscountCodeBasic {
                  title
                  summary
                  status
                }
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
            "discountCodeBasicCreate",
            graphql_mutation,
            variables={"basicCodeDiscount": discount_input},
        )

    async def get_discount_codes(self, limit: int = 25) -> str:
        """
        [Pricing & Promotions] - Get a list of discount code nodes.

        Description: Retrieves a list of all discount code nodes, which contain details about discounts.

        Required Permissions: read_discounts

        Example Usage:
        - "Show me all available discount codes." -> get_discount_codes()

        Args:
            limit (int): The maximum number of discount nodes to return.

        Returns:
            JSON string with a list of discount code nodes.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_discount_codes",
                }
            )
        graphql_query = f"\n        {{\n          codeDiscountNodes(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                codeDiscount {{\n                  ... on DiscountCodeBasic {{\n                    title\n                    summary\n                    status\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_discount_codes", graphql_query)

    async def update_basic_discount_code(
        self, discount_node_id: str, new_code: Optional[str] = None
    ) -> str:
        """
        [Pricing & Promotions] - Update a basic discount code.

        Description: Updates properties of an existing basic discount, like its code.

        Required Permissions: write_discounts

        Example Usage:
        - "Update discount 'gid://.../CodeDiscountNode/123' to use the code 'NEWCODE'." -> update_basic_discount_code(discount_node_id="gid://...", new_code="NEWCODE")

        Args:
            discount_node_id (str): The GraphQL ID of the code discount node to update.
            new_code (Optional[str]): The new discount code string.

        Returns:
            JSON string with the updated discount code data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_basic_discount_code",
                }
            )
        update_input = {}
        if new_code:
            update_input["code"] = new_code
        graphql_mutation = """
        mutation discountCodeBasicUpdate($id: ID!, $basicCodeDiscount: DiscountCodeBasicInput!) {
          discountCodeBasicUpdate(id: $id, basicCodeDiscount: $basicCodeDiscount) {
            codeDiscountNode {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": discount_node_id, "basicCodeDiscount": update_input}
        return self._execute_query(
            "discountCodeBasicUpdate", graphql_mutation, variables=variables
        )

    async def delete_discount_code(self, discount_id: str) -> str:
        """
        [Pricing & Promotions] - Delete a discount code.

        Description: Deactivates and archives a discount code, effectively deleting it.

        Required Permissions: write_discounts

        Example Usage:
        - "Delete the discount with ID 'gid://.../PriceRule/123'." -> delete_discount_code(discount_id="gid://...")

        Args:
            discount_id (str): The GraphQL ID of the discount (PriceRule) to delete.

        Returns:
            JSON string confirming the deletion or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_discount_code",
                }
            )
        graphql_mutation = """
        mutation discountDelete($id: ID!) {
          discountDelete(id: $id) {
            deletedDiscountId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "discountDelete", graphql_mutation, variables={"id": discount_id}
        )

    async def create_gift_card(
        self, initial_value: float, note: Optional[str] = None
    ) -> str:
        """
        [Pricing & Promotions] - Create a new gift card.

        Description: Issues a new gift card with a specified initial value.

        Required Permissions: write_gift_cards

        Example Usage:
        - "Create a $50 gift card for a customer giveaway." -> create_gift_card(initial_value=50.00, note="Giveaway winner")

        Args:
            initial_value (float): The initial value of the gift card.
            note (Optional[str]): An internal note for the gift card.

        Returns:
            JSON string with the new gift card's data, including the redeem code.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_gift_card",
                }
            )
        input_vars = {"initialValue": str(initial_value)}
        if note:
            input_vars["note"] = note
        graphql_mutation = """
        mutation giftCardCreate($input: GiftCardCreateInput!) {
          giftCardCreate(input: $input) {
            giftCard {
              id
              balance {
                amount
              }
              code
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "giftCardCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def get_draft_orders(
        self, status: Optional[str] = None, limit: int = 10
    ) -> str:
        """
        [Draft Orders] - Retrieve a list of draft orders.

        Description: Fetches draft orders, optionally filtering by status.

        Required Permissions: read_draft_orders

        Example Usage:
        - "Show me the last 5 open draft orders." -> get_draft_orders(status="OPEN", limit=5)

        Args:
            status (Optional[str]): Filter by status (OPEN, COMPLETED, INVOICE_SENT).
            limit (int): The maximum number of draft orders to return.

        Returns:
            JSON string with a list of draft orders.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_draft_orders",
                }
            )
        query_filter = f"status:{status}" if status else ""
        graphql_query = f'\n        {{\n          draftOrders(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                name\n                status\n                totalPrice\n                customer {{\n                  id\n                  displayName\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_draft_orders", graphql_query)

    async def get_draft_order_by_id(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Get a specific draft order by its GraphQL ID.

        Description: Retrieves detailed information for a single draft order using its GID.

        Required Permissions: read_draft_orders

        Example Usage:
        - "Get details for draft order 'gid://shopify/DraftOrder/12345'." -> get_draft_order_by_id(draft_order_id="gid://shopify/DraftOrder/12345")

        Args:
            draft_order_id (str): The full GraphQL ID of the draft order.

        Returns:
            JSON string with the draft order's details.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_draft_order_by_id",
                }
            )
        graphql_query = f'\n        {{\n          draftOrder(id: "{draft_order_id}") {{\n            id\n            name\n            status\n            note\n            totalPrice\n            lineItems(first: 10) {{\n                edges {{\n                    node {{\n                        id\n                        title\n                        quantity\n                        originalUnitPrice\n                    }}\n                }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_draft_order_by_id", graphql_query)

    async def create_draft_order(
        self,
        line_items: list[dict],
        customer_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> str:
        """
        [Draft Orders] - Create a new draft order.

        Description: Creates a draft order, which can be used to invoice customers or create orders in the admin.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Create a draft order for customer 'gid://.../Customer/123' with one 't-shirt' variant 'gid://.../Variant/456'." -> create_draft_order(line_items=[{{"variantId": "gid://.../Variant/456", "quantity": 1}}], customer_id="gid://.../Customer/123")

        Args:
            line_items (list[dict]): A list of line items, each a dict with 'variantId' and 'quantity'.
            customer_id (Optional[str]): The GraphQL ID of the customer.
            note (Optional[str]): A note for the draft order.

        Returns:
            JSON string with the created draft order's data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_draft_order",
                }
            )
        input_vars = {"lineItems": line_items}
        if customer_id:
            input_vars["customerId"] = customer_id
        if note:
            input_vars["note"] = note
        graphql_mutation = """
        mutation draftOrderCreate($input: DraftOrderInput!) {
          draftOrderCreate(input: $input) {
            draftOrder {
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
            "draftOrderCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_draft_order(self, draft_order_id: str, **kwargs) -> str:
        """
        [Draft Orders] - Update an existing draft order.

        Description: Modifies a draft order before it is completed, e.g., adding line items or updating customer info.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Add a note 'Customer wants gift wrap' to draft order 'gid://.../DraftOrder/123'." -> update_draft_order(draft_order_id="gid://.../123", note="Customer wants gift wrap")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.
            **kwargs: Fields to update (e.g., note, customerId, lineItems, shippingAddress).

        Returns:
            JSON string with the updated draft order data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_draft_order",
                }
            )
        input_vars = {key: value for key, value in kwargs.items() if value is not None}
        graphql_mutation = """
        mutation draftOrderUpdate($id: ID!, $input: DraftOrderInput!) {
          draftOrderUpdate(id: $id, input: $input) {
            draftOrder {
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
            "draftOrderUpdate",
            graphql_mutation,
            variables={"id": draft_order_id, "input": input_vars},
        )

    async def complete_draft_order(
        self, draft_order_id: str, payment_pending: bool = False
    ) -> str:
        """
        [Draft Orders] - Complete a draft order, converting it into a real order.

        Description: Finalizes a draft order. If payment is not captured, it creates an order with a pending payment.

        Required Permissions: write_draft_orders, write_orders

        Example Usage:
        - "Complete draft order 'gid://.../DraftOrder/123'." -> complete_draft_order(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.
            payment_pending (bool): Set to true if payment will be collected later.

        Returns:
            JSON string with the newly created order's ID.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "complete_draft_order",
                }
            )
        graphql_mutation = """
        mutation draftOrderComplete($id: ID!, $paymentPending: Boolean) {
          draftOrderComplete(id: $id, paymentPending: $paymentPending) {
            draftOrder {
              order {
                id
                name
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": draft_order_id, "paymentPending": payment_pending}
        return self._execute_query(
            "draftOrderComplete", graphql_mutation, variables=variables
        )

    async def send_draft_order_invoice(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Send an invoice to the customer for a draft order.

        Description: Emails an invoice to the customer associated with the draft order, allowing them to complete payment.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Send an invoice for draft order 'gid://.../DraftOrder/123'." -> send_draft_order_invoice(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.

        Returns:
            JSON string confirming the invoice was sent.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "send_draft_order_invoice",
                }
            )
        graphql_mutation = """
        mutation draftOrderInvoiceSend($id: ID!) {
          draftOrderInvoiceSend(id: $id) {
            draftOrder {
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
            "draftOrderInvoiceSend", graphql_mutation, variables={"id": draft_order_id}
        )

    async def delete_draft_order(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Delete a draft order.

        Description: Permanently deletes a draft order. This action cannot be undone.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Delete draft order 'gid://.../DraftOrder/123'." -> delete_draft_order(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order to delete.

        Returns:
            JSON string with the ID of the deleted draft order.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_draft_order",
                }
            )
        graphql_mutation = """
        mutation draftOrderDelete($id: ID!) {
          draftOrderDelete(id: $id) {
            deletedId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "draftOrderDelete", graphql_mutation, variables={"id": draft_order_id}
        )

    async def get_reports(self, limit: int = 10) -> str:
        """
        [Reports] - Retrieve a list of reports.

        Description: Fetches a list of available reports that can be generated for the store.

        Required Permissions: read_reports

        Example Usage:
        - "Show me all available reports." -> get_reports()

        Args:
            limit (int): The maximum number of reports to return.

        Returns:
            JSON string with a list of reports.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_reports",
                }
            )
        graphql_query = f"\n        {{\n          reports(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                name\n                shopifyQL\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_reports", graphql_query)

    async def get_report_by_id(self, report_id: str) -> str:
        """
        [Reports] - Get a specific report by its GraphQL ID.

        Description: Retrieves detailed information for a single report using its GID.

        Required Permissions: read_reports

        Example Usage:
        - "Get details for report 'gid://shopify/Report/12345'." -> get_report_by_id(report_id="gid://shopify/Report/12345")

        Args:
            report_id (str): The full GraphQL ID of the report.

        Returns:
            JSON string with the report's details, including its ShopifyQL query.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_report_by_id",
                }
            )
        graphql_query = f'\n        {{\n          report(id: "{report_id}") {{\n            id\n            name\n            shopifyQL\n            updatedAt\n          }}\n        }}\n        '
        return self._execute_query("get_report_by_id", graphql_query)

    async def get_blogs(self, limit: int = 10) -> str:
        """
        [Content] - Retrieve a list of blogs.

        Description: Fetches a list of all blogs in the store.

        Required Permissions: read_content

        Example Usage:
        - "Show me all the blogs in the store." -> get_blogs()

        Args:
            limit (int): The maximum number of blogs to return.

        Returns:
            JSON string with a list of blogs including their ID, title, and handle.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_blogs",
                }
            )
        graphql_query = f"\n        {{\n          blogs(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                title\n                handle\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_blogs", graphql_query)

    async def get_articles(self, blog_id: str, limit: int = 10) -> str:
        """
        [Content] - Retrieve a list of articles from a specific blog.

        Description: Fetches articles from a given blog, useful for managing content.

        Required Permissions: read_content

        Example Usage:
        - "Get the last 5 articles from blog 'gid://shopify/Blog/123'." -> get_articles(blog_id="gid://shopify/Blog/123", limit=5)

        Args:
            blog_id (str): The GraphQL ID of the blog to fetch articles from.
            limit (int): The maximum number of articles to return.

        Returns:
            JSON string with a list of articles including their ID, title, and author.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_articles",
                }
            )
        graphql_query = f'\n        {{\n          blog(id: "{blog_id}") {{\n            articles(first: {limit}) {{\n              edges {{\n                node {{\n                  id\n                  title\n                  handle\n                  authorV2 {{\n                    name\n                  }}\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_articles", graphql_query)

    async def get_article_by_id(self, article_id: str) -> str:
        """
        [Content] - Get a specific article by its GraphQL ID.

        Description: Retrieves detailed information for a single article.

        Required Permissions: read_content

        Example Usage:
        - "Show me the content of article 'gid://shopify/Article/123'." -> get_article_by_id(article_id="gid://shopify/Article/123")

        Args:
            article_id (str): The GraphQL ID of the article.

        Returns:
            JSON string with article details including title, content, and publication date.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_article_by_id",
                }
            )
        graphql_query = f'\n        {{\n          article(id: "{article_id}") {{\n            id\n            title\n            contentHtml\n            publishedAt\n          }}\n        }}\n        '
        return self._execute_query("get_article_by_id", graphql_query)

    async def create_article(
        self, blog_id: str, title: str, content_html: str, author_name: str
    ) -> str:
        """
        [Content] - Create a new article in a blog.

        Description: Publishes a new article to a specified blog.

        Required Permissions: write_content

        Example Usage:
        - "Create an article titled 'My New Post' in blog 'gid://.../Blog/123' written by 'John Doe'." -> create_article(blog_id="gid://...", title="My New Post", content_html="<p>...</p>", author_name="John Doe")

        Args:
            blog_id (str): The GraphQL ID of the blog.
            title (str): The title of the article.
            content_html (str): The article content in HTML format.
            author_name (str): The name of the author.

        Returns:
            JSON string with the created article's ID or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_article",
                }
            )
        input_vars = {
            "blogId": blog_id,
            "title": title,
            "contentHtml": content_html,
            "author": {"name": author_name},
        }
        graphql_mutation = """
        mutation blogCreateArticle($blogId: ID!, $input: ArticleInput!) {
          blogCreateArticle(blogId: $blogId, article: $input) {
            article {
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
            "blogCreateArticle",
            graphql_mutation,
            variables={"blogId": blog_id, "input": input_vars},
        )

    async def update_article(self, article_id: str, **kwargs) -> str:
        """
        [Content] - Update an existing article.

        Description: Modifies the content, title, or other properties of an article.

        Required Permissions: write_content

        Example Usage:
        - "Update the title of article 'gid://.../Article/123' to 'Updated Title'." -> update_article(article_id="gid://...", title="Updated Title")

        Args:
            article_id (str): The GraphQL ID of the article to update.
            **kwargs: Fields to update (e.g., title, contentHtml, tags).

        Returns:
            JSON string with the updated article data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_article",
                }
            )
        input_vars = {key: value for key, value in kwargs.items() if value is not None}
        graphql_mutation = """
        mutation articleUpdate($id: ID!, $input: ArticleInput!) {
          articleUpdate(id: $id, article: $input) {
            article {
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
            "articleUpdate",
            graphql_mutation,
            variables={"id": article_id, "input": input_vars},
        )

    async def delete_article(self, article_id: str) -> str:
        """
        [Content] - Delete an article.

        Description: Permanently removes an article from a blog.

        Required Permissions: write_content

        Example Usage:
        - "Delete article 'gid://.../Article/123'." -> delete_article(article_id="gid://.../Article/123")

        Args:
            article_id (str): The GraphQL ID of the article to delete.

        Returns:
            JSON string with the ID of the deleted article or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_article",
                }
            )
        graphql_mutation = """
        mutation articleDelete($id: ID!) {
          articleDelete(id: $id) {
            deletedArticleId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "articleDelete", graphql_mutation, variables={"id": article_id}
        )

    async def get_pages(self, limit: int = 10) -> str:
        """
        [Content] - Retrieve a list of online store pages.

        Description: Fetches a list of static pages like 'About Us' or 'Contact'.

        Required Permissions: read_online_store_pages

        Example Usage:
        - "Show me all the pages on the online store." -> get_pages()

        Args:
            limit (int): The maximum number of pages to return.

        Returns:
            JSON string with a list of pages including their ID, title, and handle.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_pages",
                }
            )
        graphql_query = f"\n        {{\n          pages(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                title\n                handle\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_pages", graphql_query)

    async def get_page_by_id(self, page_id: str) -> str:
        """
        [Content] - Get a specific page by its GraphQL ID.

        Description: Retrieves detailed information for a single online store page.

        Required Permissions: read_online_store_pages

        Example Usage:
        - "Get the content of page 'gid://shopify/Page/123'." -> get_page_by_id(page_id="gid://shopify/Page/123")

        Args:
            page_id (str): The GraphQL ID of the page.

        Returns:
            JSON string with page details including title and body content.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_page_by_id",
                }
            )
        graphql_query = f'\n        {{\n          page(id: "{page_id}") {{\n            id\n            title\n            body\n            bodySummary\n          }}\n        }}\n        '
        return self._execute_query("get_page_by_id", graphql_query)

    async def create_page(self, title: str, body_html: str) -> str:
        """
        [Content] - Create a new online store page.

        Description: Creates a new static page for the online store.

        Required Permissions: write_online_store_pages

        Example Usage:
        - "Create a new page called 'About Us' with some content." -> create_page(title="About Us", body_html="<p>About our company...</p>")

        Args:
            title (str): The title of the page.
            body_html (str): The page content in HTML format.

        Returns:
            JSON string with the created page's ID or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_page",
                }
            )
        input_vars = {"title": title, "bodyHtml": body_html}
        graphql_mutation = """
        mutation pageCreate($input: PageInput!) {
          pageCreate(input: $input) {
            page {
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
            "pageCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_page(self, page_id: str, **kwargs) -> str:
        """
        [Content] - Update an existing online store page.

        Description: Modifies the content or title of a page.

        Required Permissions: write_online_store_pages

        Example Usage:
        - "Update the body of page 'gid://.../Page/123' to 'New content'." -> update_page(page_id="gid://...", bodyHtml="<p>New content</p>")

        Args:
            page_id (str): The GraphQL ID of the page to update.
            **kwargs: Fields to update (e.g., title, bodyHtml).

        Returns:
            JSON string with the updated page data or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_page",
                }
            )
        input_vars = {"id": page_id}
        valid_args = ["title", "bodyHtml"]
        for key, value in kwargs.items():
            if key in valid_args and value is not None:
                input_vars[key] = value
        graphql_mutation = """
        mutation pageUpdate($input: PageInput!) {
          pageUpdate(input: $input) {
            page {
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
            "pageUpdate", graphql_mutation, variables={"input": input_vars}
        )

    async def delete_page(self, page_id: str) -> str:
        """
        [Content] - Delete an online store page.

        Description: Permanently removes a static page from the online store.

        Required Permissions: write_online_store_pages

        Example Usage:
        - "Delete the page with ID 'gid://.../Page/123'." -> delete_page(page_id="gid://.../Page/123")

        Args:
            page_id (str): The GraphQL ID of the page to delete.

        Returns:
            JSON string with the ID of the deleted page or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_page",
                }
            )
        graphql_mutation = """
        mutation pageDelete($input: PageDeleteInput!) {
          pageDelete(input: $input) {
            deletedPageId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "pageDelete", graphql_mutation, variables={"input": {"id": page_id}}
        )

    async def get_marketing_events(self, limit: int = 10) -> str:
        """
        [Marketing] - Retrieve a list of marketing events.

        Description: Fetches a list of marketing events, which represent activities like ad campaigns or social media posts.

        Required Permissions: read_marketing_events

        Example Usage:
        - "Show me the last 5 marketing events." -> get_marketing_events(limit=5)

        Args:
            limit (int): The maximum number of events to return.

        Returns:
            JSON string with a list of marketing events.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_marketing_events",
                }
            )
        graphql_query = f"\n        {{\n          marketingEvents(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                appTitle\n                description\n                type\n                startedAt\n                endedAt\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_marketing_events", graphql_query)

    async def get_marketing_event_by_id(self, event_id: str) -> str:
        """
        [Marketing] - Get a specific marketing event by its GraphQL ID.

        Description: Retrieves detailed information for a single marketing event using its GID.

        Required Permissions: read_marketing_events

        Example Usage:
        - "Get details for marketing event 'gid://shopify/MarketingEvent/123'." -> get_marketing_event_by_id(event_id="gid://shopify/MarketingEvent/123")

        Args:
            event_id (str): The full GraphQL ID of the marketing event.

        Returns:
            JSON string with the marketing event's details.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_marketing_event_by_id",
                }
            )
        graphql_query = f'\n        {{\n          marketingEvent(id: "{event_id}") {{\n            id\n            appTitle\n            description\n            type\n            startedAt\n            endedAt\n            utmCampaign\n          }}\n        }}\n        '
        return self._execute_query("get_marketing_event_by_id", graphql_query)

    async def create_marketing_event(self, event_input: dict) -> str:
        """
        [Marketing] - Create a new marketing event.

        Description: Logs a new marketing event to track campaign activities. The input must be a dictionary matching Shopify's MarketingEventInput schema.

        Required Permissions: write_marketing_events

        Example Usage:
        - "Create a marketing event for our 'Summer Sale' campaign." -> create_marketing_event(event_input={{"type": "AD", "startedAt": "2024-07-01T00:00:00Z", "utmCampaign": "summer_sale_24"}})

        Args:
            event_input (dict): A dictionary representing the MarketingEventInput object.

        Returns:
            JSON string with the created marketing event's ID.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_marketing_event",
                }
            )
        graphql_mutation = """
        mutation marketingEventCreate($marketingEvent: MarketingEventInput!) {
          marketingEventCreate(marketingEvent: $marketingEvent) {
            marketingEvent {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "marketingEventCreate",
            graphql_mutation,
            variables={"marketingEvent": event_input},
        )

    async def update_marketing_event(self, event_id: str, event_input: dict) -> str:
        """
        [Marketing] - Update an existing marketing event.

        Description: Modifies an existing marketing event. The input must be a dictionary matching Shopify's MarketingEventInput schema.

        Required Permissions: write_marketing_events

        Example Usage:
        - "Update the end date for marketing event 'gid://.../123'." -> update_marketing_event(event_id="gid://.../123", event_input={{"endedAt": "2024-07-31T23:59:59Z"}})

        Args:
            event_id (str): The GraphQL ID of the marketing event to update.
            event_input (dict): A dictionary representing the MarketingEventInput object with fields to update.

        Returns:
            JSON string with the updated marketing event's ID.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_marketing_event",
                }
            )
        graphql_mutation = """
        mutation marketingEventUpdate($id: ID!, $marketingEvent: MarketingEventInput!) {
          marketingEventUpdate(id: $id, marketingEvent: $marketingEvent) {
            marketingEvent {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": event_id, "marketingEvent": event_input}
        return self._execute_query(
            "marketingEventUpdate", graphql_mutation, variables=variables
        )

    async def delete_marketing_event(self, event_id: str) -> str:
        """
        [Marketing] - Delete a marketing event.

        Description: Permanently removes a marketing event.

        Required Permissions: write_marketing_events

        Example Usage:
        - "Delete the marketing event 'gid://.../MarketingEvent/456'." -> delete_marketing_event(event_id="gid://.../456")

        Args:
            event_id (str): The GraphQL ID of the marketing event to delete.

        Returns:
            JSON string with the ID of the deleted event.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_marketing_event",
                }
            )
        graphql_mutation = """
        mutation marketingEventDelete($id: ID!) {
          marketingEventDelete(id: $id) {
            deletedId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "marketingEventDelete", graphql_mutation, variables={"id": event_id}
        )

    async def get_locations(self, limit: int = 25) -> str:
        """
        [Locations] - List all fulfillment locations.

        Description: Retrieves stores, warehouses, and pop-up locations used for inventory and fulfillment.

        Required Permissions: read_locations

        Example Usage:
        - "Show me all store locations." -> get_locations()
        - "List the first 10 locations." -> get_locations(limit=10)

        Args:
            limit (int): Maximum number of locations to return (1-250).

        Returns:
            JSON string with a list of locations including id, name, address, and active status.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_locations",
                }
            )
        graphql_query = f"\n        {{\n          locations(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                name\n                address {{\n                  address1\n                  city\n                  zip\n                  countryCodeV2\n                }}\n                isActive\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_locations", graphql_query)

    async def get_location_by_id(self, location_id: str) -> str:
        """
        [Locations] - Retrieve a specific location by its GraphQL ID.

        Description: Fetches detailed information for a single location, including its fulfillment capabilities.

        Required Permissions: read_locations

        Example Usage:
        - "Get details for location 'gid://shopify/Location/123'." -> get_location_by_id(location_id="gid://shopify/Location/123")

        Args:
            location_id (str): The GraphQL ID of the location.

        Returns:
            JSON string with detailed location information.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_location_by_id",
                }
            )
        graphql_query = f'\n        {{\n          location(id: "{location_id}") {{\n            id\n            name\n            address {{\n                address1\n                address2\n                city\n                zip\n                province\n                country\n            }}\n            fulfillsOnlineOrders\n          }}\n        }}\n        '
        return self._execute_query("get_location_by_id", graphql_query)

    async def activate_location(self, location_id: str) -> str:
        """
        [Locations] - Activate a location for fulfillment.

        Description: Enables a disabled location, allowing it to be used for fulfilling orders.

        Required Permissions: write_locations

        Example Usage:
        - "Activate location 'gid://shopify/Location/456'." -> activate_location(location_id="gid://shopify/Location/456")

        Args:
            location_id (str): The GraphQL ID of the location to activate.

        Returns:
            JSON string confirming the location was activated or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "activate_location",
                }
            )
        graphql_mutation = """
        mutation locationActivate($id: ID!) {
          locationActivate(id: $id) {
            location {
              id
              isActive
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "locationActivate", graphql_mutation, variables={"id": location_id}
        )

    async def deactivate_location(self, location_id: str) -> str:
        """
        [Locations] - Deactivate a location.

        Description: Disables an active location, preventing it from being used for new fulfillments.

        Required Permissions: write_locations

        Example Usage:
        - "Deactivate location 'gid://shopify/Location/789'." -> deactivate_location(location_id="gid://shopify/Location/789")

        Args:
            location_id (str): The GraphQL ID of the location to deactivate.

        Returns:
            JSON string confirming the location was deactivated or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "deactivate_location",
                }
            )
        graphql_mutation = """
        mutation locationDeactivate($id: ID!) {
          locationDeactivate(id: $id) {
            location {
              id
              isActive
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "locationDeactivate", graphql_mutation, variables={"id": location_id}
        )

    async def get_returns(self, limit: int = 10) -> str:
        """
        [Returns] - Retrieve a list of returns.

        Description: Fetches a list of all returns, which represent requests by customers to return items.

        Required Permissions: read_returns

        Example Usage:
        - "Show me the last 10 returns." -> get_returns(limit=10)

        Args:
            limit (int): The maximum number of returns to retrieve.

        Returns:
            JSON string with a list of returns including their status and associated order.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_returns",
                }
            )
        graphql_query = f"\n        {{\n          returns(first: {limit}) {{\n            edges {{\n              node {{\n                id\n                name\n                status\n                order {{\n                  id\n                  name\n                }}\n              }}\n            }}\n          }}\n        }}\n        "
        return self._execute_query("get_returns", graphql_query)

    async def get_return_by_id(self, return_id: str) -> str:
        """
        [Returns] - Retrieve a specific return by its GraphQL ID.

        Description: Fetches detailed information for a single return, including its line items and status.

        Required Permissions: read_returns

        Example Usage:
        - "Get details for return 'gid://shopify/Return/123'." -> get_return_by_id(return_id="gid://shopify/Return/123")

        Args:
            return_id (str): The GraphQL ID of the return.

        Returns:
            JSON string with detailed return information.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_return_by_id",
                }
            )
        graphql_query = f'\n        {{\n          return(id: "{return_id}") {{\n            id\n            name\n            status\n            returnLineItems(first: 10) {{\n              edges {{\n                node {{\n                  id\n                  quantity\n                  returnReason\n                  customerNote\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_return_by_id", graphql_query)

    async def create_return(self, order_id: str, return_line_items: list[dict]) -> str:
        """
        [Returns] - Initiate a return for an order.

        Description: Creates a return request for one or more items from a specified order.

        Required Permissions: write_returns

        Example Usage:
        - "Start a return for order 'gid://.../Order/123' for 1 unit of item 'gid://.../LineItem/456'." -> create_return(order_id="gid://.../123", return_line_items=[{{"fulfillmentLineItemId": "gid://.../456", "quantity": 1}}])

        Args:
            order_id (str): The GraphQL ID of the order being returned.
            return_line_items (list[dict]): A list of items to return, each a dict with 'fulfillmentLineItemId' and 'quantity'.

        Returns:
            JSON string with the newly created return's data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_return",
                }
            )
        input_vars = {"orderId": order_id, "returnLineItems": return_line_items}
        graphql_mutation = """
        mutation returnRequest($input: ReturnRequestInput!) {
          returnRequest(input: $input) {
            return {
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
            "returnRequest", graphql_mutation, variables={"input": input_vars}
        )

    async def approve_return(self, return_id: str, note: Optional[str] = None) -> str:
        """
        [Returns] - Approve a return request.

        Description: Marks a return as approved, allowing the customer to proceed with sending back the items.

        Required Permissions: write_returns

        Example Usage:
        - "Approve return 'gid://shopify/Return/123'." -> approve_return(return_id="gid://shopify/Return/123")

        Args:
            return_id (str): The GraphQL ID of the return to approve.
            note (Optional[str]): An optional note for the approval.

        Returns:
            JSON string confirming the return was approved.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "approve_return",
                }
            )
        variables = {"id": return_id, "note": note}
        graphql_mutation = """
        mutation returnApprove($id: ID!, $note: String) {
          returnApprove(id: $id, note: $note) {
            return {
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
            "returnApprove", graphql_mutation, variables=variables
        )

    async def decline_return(
        self, return_id: str, reason: str, note: Optional[str] = None
    ) -> str:
        """
        [Returns] - Decline a return request.

        Description: Rejects a customer's return request, with a mandatory reason.

        Required Permissions: write_returns

        Example Usage:
        - "Decline return 'gid://.../Return/123' because it's past the return window." -> decline_return(return_id="gid://.../123", reason="POLICY_VIOLATION", note="Item returned after 30-day policy.")

        Args:
            return_id (str): The GraphQL ID of the return to decline.
            reason (str): The reason for declining (e.g., POLICY_VIOLATION, OTHER).
            note (Optional[str]): An optional note with more details.

        Returns:
            JSON string confirming the return was declined.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "decline_return",
                }
            )
        variables = {"id": return_id, "declineReason": reason, "note": note}
        graphql_mutation = """
        mutation returnDecline($id: ID!, $declineReason: ReturnDeclineReason!, $note: String) {
          returnDecline(id: $id, declineReason: $declineReason, note: $note) {
            return {
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
            "returnDecline", graphql_mutation, variables=variables
        )

    async def close_return(self, return_id: str, note: Optional[str] = None) -> str:
        """
        [Returns] - Close a return.

        Description: Finalizes a return process after items have been received or the process is otherwise complete.

        Required Permissions: write_returns

        Example Usage:
        - "Close return 'gid://.../Return/123'." -> close_return(return_id="gid://.../123")

        Args:
            return_id (str): The GraphQL ID of the return to close.
            note (Optional[str]): An optional note for closing the return.

        Returns:
            JSON string confirming the return was closed.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "close_return",
                }
            )
        variables = {"id": return_id, "note": note}
        graphql_mutation = """
        mutation returnClose($id: ID!, $note: String) {
          returnClose(id: $id, note: $note) {
            return {
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
        return self._execute_query("closeReturn", graphql_mutation, variables=variables)

    async def create_staged_upload(
        self, filename: str, mime_type: str, resource: str = "IMAGE"
    ) -> str:
        """
        [Files & Media Management] - Step 1/2 for File Upload. Creates a staged upload target.

        Description: This is the first step to upload a file. It prepares a secure, temporary URL where the file can be uploaded via an HTTP request. After a successful response from this tool, the file must be uploaded to the `url` provided in the response. Finally, call `file_create` with the `resourceUrl` to complete the process.

        Required Permissions: write_files

        Example Usage:
        - "Prepare to upload a new product image named 'tshirt.jpg'." -> create_staged_upload(filename='tshirt.jpg', mime_type='image/jpeg', resource='IMAGE')

        Args:
            filename (str): The name of the file to be uploaded.
            mime_type (str): The MIME type of the file (e.g., 'image/jpeg', 'application/pdf').
            resource (str): The type of resource. Defaults to 'IMAGE'. Valid values: IMAGE, VIDEO, THREED_MODEL, FILE.

        Returns:
            JSON string with the staged upload target details, including `url` for upload and `resourceUrl` for `file_create`.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_staged_upload",
                }
            )
        input_vars = {
            "input": [
                {
                    "filename": filename,
                    "mimeType": mime_type,
                    "resource": resource,
                    "httpMethod": "PUT",
                }
            ]
        }
        graphql_mutation = """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
            stagedUploadsCreate(input: $input) {
                stagedTargets {
                    url
                    resourceUrl
                    parameters {
                        name
                        value
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
            "stagedUploadsCreate", graphql_mutation, variables=input_vars
        )

    async def file_create(self, original_source: str, content_type: str) -> str:
        """
        [Files & Media Management] - Step 2/2 for File Upload. Commits a file after staged upload.

        Description: This is the final step to upload a file. After the file has been uploaded to the temporary URL from `create_staged_upload`, this tool registers it with Shopify, making it accessible in the Files section of the admin.

        Required Permissions: write_files

        Example Usage:
        - "Finalize the upload for the file located at 'resourceUrl_from_staged_upload'." -> file_create(original_source='resourceUrl_from_staged_upload', content_type='IMAGE')

        Args:
            original_source (str): The `resourceUrl` returned by the `create_staged_upload` tool.
            content_type (str): The content type of the file. Valid values: IMAGE, VIDEO, THREED_MODEL, FILE.

        Returns:
            JSON string with the newly created file's details or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "file_create",
                }
            )
        input_vars = {
            "files": [{"originalSource": original_source, "contentType": content_type}]
        }
        graphql_mutation = """
        mutation fileCreate($files: [FileCreateInput!]!) {
            fileCreate(files: $files) {
                files {
                    id
                    fileStatus
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        return self._execute_query("fileCreate", graphql_mutation, variables=input_vars)

    async def get_files(self, limit: int = 25) -> str:
        """
        [Files & Media Management] - Retrieve a list of files from the store.

        Description: Fetches a list of all uploaded files (images, videos, documents) in the Shopify admin.

        Required Permissions: read_files

        Example Usage:
        - "Show me the last 10 files uploaded to the store." -> get_files(limit=10)

        Args:
            limit (int): The maximum number of files to return (1-250).

        Returns:
            JSON string with a list of files, including their ID, filename, and URL.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_files",
                }
            )
        graphql_query = f" \n        {{\n            files(first: {limit}) {{\n                edges {{\n                    node {{\n                        ... on MediaImage {{\n                            id\n                            image {{\n                                url\n                            }}\n                        }}\n                        ... on GenericFile {{\n                            id\n                            url\n                        }}\n                        ... on Video {{\n                            id\n                            originalSource {{\n                                url\n                            }}\n                        }}\n                    }}\n                }}\n            }}\n        }}\n        "
        return self._execute_query("get_files", graphql_query)

    async def delete_files(self, file_ids: list[str]) -> str:
        """
        [Files & Media Management] - Delete one or more files from the store.

        Description: Permanently removes files from the Shopify admin based on their GraphQL IDs.

        Required Permissions: write_files

        Example Usage:
        - "Delete the file with ID 'gid://shopify/GenericFile/12345'." -> delete_files(file_ids=['gid://shopify/GenericFile/12345'])

        Args:
            file_ids (list[str]): A list of file GraphQL IDs to be deleted.

        Returns:
            JSON string with the IDs of the deleted files or an error message.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_files",
                }
            )
        variables = {"fileIds": file_ids}
        graphql_mutation = """
        mutation fileDelete($fileIds: [ID!]!) {
            fileDelete(fileIds: $fileIds) {
                deletedFileIds
                userErrors {
                    field
                    message
                }
            }
        }
        """
        return self._execute_query("fileDelete", graphql_mutation, variables=variables)

    async def get_draft_orders(
        self, status: Optional[str] = None, limit: int = 10
    ) -> str:
        """
        [Draft Orders] - Retrieve a list of draft orders.

        Description: Fetches draft orders, optionally filtering by status.

        Required Permissions: read_draft_orders

        Example Usage:
        - "Show me the last 5 open draft orders." -> get_draft_orders(status="OPEN", limit=5)

        Args:
            status (Optional[str]): Filter by status (OPEN, COMPLETED, INVOICE_SENT).
            limit (int): The maximum number of draft orders to return.

        Returns:
            JSON string with a list of draft orders.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_draft_orders",
                }
            )
        query_filter = f"status:{status}" if status else ""
        graphql_query = f'\n        {{\n          draftOrders(first: {limit}, query: "{query_filter}") {{\n            edges {{\n              node {{\n                id\n                name\n                status\n                totalPrice\n                customer {{\n                  id\n                  displayName\n                }}\n              }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_draft_orders", graphql_query)

    async def get_draft_order_by_id(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Get a specific draft order by its GraphQL ID.

        Description: Retrieves detailed information for a single draft order using its GID.

        Required Permissions: read_draft_orders

        Example Usage:
        - "Get details for draft order 'gid://shopify/DraftOrder/12345'." -> get_draft_order_by_id(draft_order_id="gid://shopify/DraftOrder/12345")

        Args:
            draft_order_id (str): The full GraphQL ID of the draft order.

        Returns:
            JSON string with the draft order's details.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "get_draft_order_by_id",
                }
            )
        graphql_query = f'\n        {{\n          draftOrder(id: "{draft_order_id}") {{\n            id\n            name\n            status\n            note\n            totalPrice\n            lineItems(first: 10) {{\n                edges {{\n                    node {{\n                        id\n                        title\n                        quantity\n                        originalUnitPrice\n                    }}\n                }}\n            }}\n          }}\n        }}\n        '
        return self._execute_query("get_draft_order_by_id", graphql_query)

    async def create_draft_order(
        self,
        line_items: list[dict],
        customer_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> str:
        """
        [Draft Orders] - Create a new draft order.

        Description: Creates a draft order, which can be used to invoice customers or create orders in the admin.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Create a draft order for customer 'gid://.../Customer/123' with one 't-shirt' variant 'gid://.../Variant/456'." -> create_draft_order(line_items=[{{"variantId": "gid://.../Variant/456", "quantity": 1}}], customer_id="gid://.../Customer/123")

        Args:
            line_items (list[dict]): A list of line items, each a dict with 'variantId' and 'quantity'.
            customer_id (Optional[str]): The GraphQL ID of the customer.
            note (Optional[str]): A note for the draft order.

        Returns:
            JSON string with the created draft order's data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "create_draft_order",
                }
            )
        input_vars = {"lineItems": line_items}
        if customer_id:
            input_vars["customerId"] = customer_id
        if note:
            input_vars["note"] = note
        graphql_mutation = """
        mutation draftOrderCreate($input: DraftOrderInput!) {
          draftOrderCreate(input: $input) {
            draftOrder {
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
            "draftOrderCreate", graphql_mutation, variables={"input": input_vars}
        )

    async def update_draft_order(self, draft_order_id: str, **kwargs) -> str:
        """
        [Draft Orders] - Update an existing draft order.

        Description: Modifies a draft order before it is completed, e.g., adding line items or updating customer info.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Add a note 'Customer wants gift wrap' to draft order 'gid://.../DraftOrder/123'." -> update_draft_order(draft_order_id="gid://.../123", note="Customer wants gift wrap")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.
            **kwargs: Fields to update (e.g., note, customerId, lineItems, shippingAddress).

        Returns:
            JSON string with the updated draft order data.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "update_draft_order",
                }
            )
        input_vars = {key: value for key, value in kwargs.items() if value is not None}
        graphql_mutation = """
        mutation draftOrderUpdate($id: ID!, $input: DraftOrderInput!) {
          draftOrderUpdate(id: $id, input: $input) {
            draftOrder {
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
            "draftOrderUpdate",
            graphql_mutation,
            variables={"id": draft_order_id, "input": input_vars},
        )

    async def complete_draft_order(
        self, draft_order_id: str, payment_pending: bool = False
    ) -> str:
        """
        [Draft Orders] - Complete a draft order, converting it into a real order.

        Description: Finalizes a draft order. If payment is not captured, it creates an order with a pending payment.

        Required Permissions: write_draft_orders, write_orders

        Example Usage:
        - "Complete draft order 'gid://.../DraftOrder/123'." -> complete_draft_order(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.
            payment_pending (bool): Set to true if payment will be collected later.

        Returns:
            JSON string with the newly created order's ID.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "complete_draft_order",
                }
            )
        graphql_mutation = """
        mutation draftOrderComplete($id: ID!, $paymentPending: Boolean) {
          draftOrderComplete(id: $id, paymentPending: $paymentPending) {
            draftOrder {
              order {
                id
                name
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        variables = {"id": draft_order_id, "paymentPending": payment_pending}
        return self._execute_query(
            "draftOrderComplete", graphql_mutation, variables=variables
        )

    async def send_draft_order_invoice(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Send an invoice to the customer for a draft order.

        Description: Emails an invoice to the customer associated with the draft order, allowing them to complete payment.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Send an invoice for draft order 'gid://.../DraftOrder/123'." -> send_draft_order_invoice(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order.

        Returns:
            JSON string confirming the invoice was sent.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "send_draft_order_invoice",
                }
            )
        graphql_mutation = """
        mutation draftOrderInvoiceSend($id: ID!) {
          draftOrderInvoiceSend(id: $id) {
            draftOrder {
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
            "draftOrderInvoiceSend", graphql_mutation, variables={"id": draft_order_id}
        )

    async def delete_draft_order(self, draft_order_id: str) -> str:
        """
        [Draft Orders] - Delete a draft order.

        Description: Permanently deletes a draft order. This action cannot be undone.

        Required Permissions: write_draft_orders

        Example Usage:
        - "Delete draft order 'gid://.../DraftOrder/123'." -> delete_draft_order(draft_order_id="gid://.../123")

        Args:
            draft_order_id (str): The GraphQL ID of the draft order to delete.

        Returns:
            JSON string with the ID of the deleted draft order.
        """
        session = await get_shopify_session()
        if not session:
            return json.dumps(
                {
                    "success": False,
                    "error": "Shopify session not available. Check credentials.",
                    "tool": "delete_draft_order",
                }
            )
        graphql_mutation = """
        mutation draftOrderDelete($id: ID!) {
          draftOrderDelete(id: $id) {
            deletedId
            userErrors {
              field
              message
            }
          }
        }
        """
        return self._execute_query(
            "draftOrderDelete", graphql_mutation, variables={"id": draft_order_id}
        )