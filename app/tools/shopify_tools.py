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