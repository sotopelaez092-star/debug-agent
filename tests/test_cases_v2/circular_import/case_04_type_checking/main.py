"""Test type checking circular imports: Domain <-> DTO <-> Services."""
from services import UserService, OrderService, ProductService
from dto import UserCreateDTO, OrderCreateDTO


def main():
    # Initialize services
    user_service = UserService()
    order_service = OrderService()
    product_service = ProductService()

    # Create users
    user1_dto = UserCreateDTO("u1", "alice", "alice@example.com")
    user1 = user_service.create_user(user1_dto)
    print(f"Created user: {user1.username} ({user1.email})")

    user2_dto = UserCreateDTO("u2", "bob", "bob@example.com")
    user2 = user_service.create_user(user2_dto)
    print(f"Created user: {user2.username} ({user2.email})")

    # Create products
    product1 = product_service.create_product("p1", "Laptop", 999.99, 10)
    product2 = product_service.create_product("p2", "Mouse", 29.99, 50)
    print(f"Created products: {product1.name}, {product2.name}")

    # Create orders
    order1_dto = OrderCreateDTO("o1", "u1", [
        {"product_id": "p1", "quantity": 1, "price": 999.99},
        {"product_id": "p2", "quantity": 2, "price": 29.99}
    ])
    order1 = order_service.create_order(order1_dto)
    print(f"Created order {order1.order_id}: ${order1.total}")

    # Get all users
    all_users = user_service.get_all_users()
    print(f"Total users: {len(all_users)}")

    # Get user orders
    user_orders = order_service.get_user_orders("u1")
    print(f"User u1 has {len(user_orders)} orders")

    # Confirm order
    order_service.confirm_order("o1")
    confirmed_order = order_service.get_order("o1")
    print(f"Order status: {confirmed_order.status}")

    # Deactivate user
    user_service.deactivate_user("u2")
    print("User u2 deactivated")


if __name__ == "__main__":
    main()
