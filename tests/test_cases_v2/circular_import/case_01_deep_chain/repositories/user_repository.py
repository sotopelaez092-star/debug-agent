from typing import Dict, Optional, List
from models import User


class UserRepository:
    def __init__(self):
        self._users: Dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def find_all(self) -> List[User]:
        return list(self._users.values())

    def delete(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False
