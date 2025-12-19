"""Test lazy import circular dependency: Engine -> Drivers -> Config -> Engine."""
from engine import QueryExecutor, QueryOptimizer
from config import ConfigValidator


def main():
    # Initialize query executor
    executor = QueryExecutor()

    # Execute some queries
    result = executor.execute("SELECT * FROM users", "postgres")
    print(f"Postgres query result: {result}")

    # Execute Redis commands
    redis_result = executor.execute("SET user:1 john", "redis")
    print(f"Redis command result: {redis_result}")

    # Get driver status
    postgres_status = executor.get_driver_status("postgres")
    print(f"Postgres status: {postgres_status}")

    # Optimize queries
    optimizer = QueryOptimizer()
    optimized = optimizer.optimize("SELECT name FROM products")
    print(f"Optimized query: {optimized}")

    # Validate configuration
    validator = ConfigValidator()
    validation = validator.validate()
    print(f"Configuration validation: {validation}")

    recommendations = validator.get_recommendations()
    print(f"Recommendations: {recommendations}")

    # Execute batch queries
    queries = [
        "SELECT * FROM orders",
        "SELECT * FROM products",
        "SELECT * FROM customers"
    ]
    batch_results = executor.execute_batch(queries, "postgres")
    print(f"Executed {len(batch_results)} queries in batch")


if __name__ == "__main__":
    main()
