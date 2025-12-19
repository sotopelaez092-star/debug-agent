#!/usr/bin/env python3
def validate_input(value):
    """验证输入"""
    return value is not None and len(str(value)) > 0

def main():
    user_input = "test"
    # 拼写错误：validat_inpt (少了 e, u)
    if validat_inpt(user_input):
        print(f"Valid: {user_input}")

if __name__ == "__main__":
    main()
