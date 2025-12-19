"""
Order processing module.
Handles order data processing - also expects OLD snake_case keys.
"""
from typing import Dict, Any, List


class OrderProcessor:
    """Processes order data."""

    def process_order(self, order_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process order dictionary.
        Expects OLD snake_case keys (order_id, user_id, total_amount, etc.)
        """
        # Extract order fields using OLD key names
        order_id = order_dict['order_id']  # KeyError: expects 'order_id'
        user_id = order_dict['user_id']  # KeyError: expects 'user_id'
        total_amount = order_dict['total_amount']  # KeyError: expects 'total_amount'
        status = order_dict['order_status']  # KeyError: expects 'order_status'

        return {
            'id': order_id,
            'customer_id': user_id,
            'amount': total_amount,
            'status': status
        }

    def calculate_order_total(self, order_dict: Dict[str, Any]) -> float:
        """Calculate order total with tax."""
        base_amount = order_dict['total_amount']  # KeyError
        tax_rate = 0.08
        return base_amount * (1 + tax_rate)

    def get_shipping_info(self, order_dict: Dict[str, Any]) -> Dict[str, str]:
        """Extract shipping information from order."""
        if 'shipping_address' not in order_dict:  # KeyError: expects 'shipping_address'
            return {}

        address = order_dict['shipping_address']
        return {
            'city': address['city'],
            'state': address['state'],
            'zip': address['zip_code']  # KeyError: expects 'zip_code' but gets 'zipCode'
        }

    def get_order_summary(self, order_dict: Dict[str, Any]) -> str:
        """Generate order summary string."""
        order_id = order_dict['order_id']  # KeyError
        status = order_dict['order_status']  # KeyError
        items_count = len(order_dict['items'])

        return f"Order {order_id}: {items_count} items, status={status}"
