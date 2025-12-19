from typing import Optional, List
from models import Product
from repositories import ProductRepository
# CIRCULAR IMPORT: ProductService needs NotificationService for stock alerts
from services.notification_service import NotificationService


class ProductService:
    def __init__(self):
        self._repo = ProductRepository()
        self._notification_service = NotificationService()

    def create_product(self, product_id: str, name: str, price: float, stock: int = 0) -> Product:
        product = Product(id=product_id, name=name, price=price, stock=stock)
        self._repo.save(product)
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._repo.find_by_id(product_id)

    def update_stock(self, product_id: str, quantity: int) -> bool:
        product = self._repo.find_by_id(product_id)
        if product:
            product.stock = quantity
            if quantity < 10:
                self._notification_service.send_low_stock_alert(product)
            return True
        return False

    def list_available(self) -> List[Product]:
        return self._repo.find_available()
