import reflex as rx
from typing import TypedDict, Optional


class VariantOption(TypedDict):
    name: str
    value: str


class ProductVariantState(rx.State):
    """Manages the state for creating and updating product variants."""

    show_variant_modal: bool = False
    product_id_for_variant: Optional[str] = None
    variant_id_for_edit: Optional[str] = None
    variant_price: str = ""
    variant_sku: str = ""
    variant_options: list[str] = []

    @rx.event
    def open_variant_modal(self, product_id: str, variant_id: Optional[str] = None):
        """Open the modal to add or edit a variant."""
        self.product_id_for_variant = product_id
        self.variant_id_for_edit = variant_id
        self.variant_price = ""
        self.variant_sku = ""
        self.variant_options = []
        self.show_variant_modal = True

    @rx.event
    def close_variant_modal(self):
        """Close the variant modal."""
        self.show_variant_modal = False
        self.product_id_for_variant = None
        self.variant_id_for_edit = None

    @rx.event
    def add_option(self):
        """Adds a new empty option to the variant form."""
        self.variant_options.append("")

    @rx.event
    def update_option(self, index: int, value: str):
        """Updates an option value at a specific index."""
        if 0 <= index < len(self.variant_options):
            self.variant_options[index] = value

    @rx.event
    def remove_option(self, index: int):
        """Removes an option from the variant form."""
        if 0 <= index < len(self.variant_options):
            self.variant_options.pop(index)

    @rx.event
    async def save_variant(self):
        """Saves the new or updated variant by calling the appropriate tool."""
        from app.tools.shopify_tools import ShopifyTools

        tools = ShopifyTools()
        if self.variant_id_for_edit:
            kwargs = {}
            if self.variant_price:
                kwargs["price"] = self.variant_price
            if self.variant_sku:
                kwargs["sku"] = self.variant_sku
            if self.variant_options:
                kwargs["options"] = self.variant_options
            print(f"Updating variant {self.variant_id_for_edit} with {kwargs}")
        elif self.product_id_for_variant:
            print(
                f"Creating variant for product {self.product_id_for_variant} with price: {self.variant_price}, sku: {self.variant_sku}, options: {self.variant_options}"
            )
        self.close_variant_modal()