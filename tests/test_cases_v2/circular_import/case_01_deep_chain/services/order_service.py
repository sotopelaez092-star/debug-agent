from typing import Optional, List
from models import Order, OrderItem
from repositories import OrderRepository
# CIRCULAR IMPORT: OrderService needs ProductService for stock check
from services.product_service import ProductService


class OrderService:
    def __init__(self):
        self._repo = OrderRepository()
        self._product_service = ProductService()

    def create_order(self, order_id: str, user_id: str, items: List[dict]) -> Order:
        order_items = []
        for item in items:
            product = self._product_service.get_product(item["product_id"])
            if product and product.is_available():
                order_items.append(OrderItem(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=product.price
                ))

        order = Order(id=order_id, user_id=user_id, items=order_items)
        self._repo.save(order)
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._repo.find_by_id(order_id)

    def get_orders_for_user(self, user_id: str) -> List[Order]:
        return self._repo.find_by_user_id(user_id)
