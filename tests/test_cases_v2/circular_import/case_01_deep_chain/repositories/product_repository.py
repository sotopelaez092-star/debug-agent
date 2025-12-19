from typing import Dict, Optional, List
from models import Product


class ProductRepository:
    def __init__(self):
        self._products: Dict[str, Product] = {}

    def save(self, product: Product) -> None:
        self._products[product.id] = product

    def find_by_id(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    def find_all(self) -> List[Product]:
        return list(self._products.values())

    def find_available(self) -> List[Product]:
        return [p for p in self._products.values() if p.is_available()]
