#!/usr/bin/env python3
def calculate_sum(numbers):
    """计算数字列表的和"""
    return sum(numbers)

def main():
    data = [1, 2, 3, 4, 5]
    # 拼写错误：calculate_summ (多了一个 m)
    result = calculate_summ(data)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
