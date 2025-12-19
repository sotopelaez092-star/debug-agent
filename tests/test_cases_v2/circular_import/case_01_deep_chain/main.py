"""Test deep circular import chain across 4 services."""
from services import UserService, OrderService, ProductService


def main():
    # Create services
    user_service = UserService()
    product_service = ProductService()
    order_service = OrderService()

    # Create a user
    user = user_service.create_user("u1", "Alice", "alice@example.com")
    print(f"Created user: {user.name}")

    # Create some products
    product1 = product_service.create_product("p1", "Laptop", 999.99, stock=5)
    product2 = product_service.create_product("p2", "Mouse", 29.99, stock=50)
    print(f"Created products: {product1.name}, {product2.name}")

    # Create an order
    order = order_service.create_order("o1", "u1", [
        {"product_id": "p1", "quantity": 1},
        {"product_id": "p2", "quantity": 2},
    ])
    print(f"Created order: {order.id}, total: ${order.total:.2f}")

    # Update stock (will trigger low stock alert)
    product_service.update_stock("p1", 3)

    # Get user with orders
    user_with_orders = user_service.get_user_with_orders("u1")
    print(f"User {user_with_orders.name} has {len(user_with_orders.orders)} orders")


if __name__ == "__main__":
    main()
