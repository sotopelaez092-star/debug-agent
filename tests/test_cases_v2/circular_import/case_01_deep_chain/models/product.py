from typing import Optional
from dataclasses import dataclass


@dataclass
class Product:
    id: str
    name: str
    price: float
    stock: int = 0

    def is_available(self) -> bool:
        return self.stock > 0
