"""Product service."""
from typing import List, Optional
from domain import Product


class ProductService:
    """Business logic for product operations."""

    def __init__(self):
        self._products: dict = {}

    def create_product(self, product_id: str, name: str, price: float, stock: int) -> Product:
        """Create a new product."""
        product = Product(product_id, name, price, stock)
        self._products[product_id] = product
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self._products.get(product_id)

    def get_all_products(self) -> List[Product]:
        """Get all products."""
        return list(self._products.values())

    def reserve_product(self, product_id: str, quantity: int) -> bool:
        """Reserve product stock."""
        product = self._products.get(product_id)
        if product:
            return product.reserve(quantity)
        return False

    def check_availability(self, product_id: str) -> bool:
        """Check if product is available."""
        product = self._products.get(product_id)
        return product.is_available() if product else False
