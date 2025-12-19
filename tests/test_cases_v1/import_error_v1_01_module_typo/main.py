#!/usr/bin/env python3
# 拼写错误：authentification (多了 i，少了 c)
from authentification import verify_user

def main():
    user = "alice"
    if verify_user(user):
        print(f"Welcome {user}!")

if __name__ == "__main__":
    main()
