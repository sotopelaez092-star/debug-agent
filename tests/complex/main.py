from models import User
from utils import calculate_discount

def main():
    user = User("Tom", 25)
    print(calculate_discount(user))  # 错误：calculate_discount未定义

if __name__ == "__main__":
    main()