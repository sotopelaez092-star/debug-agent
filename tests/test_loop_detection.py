def calculate_sum(numbers):
    # 故意制造一个可能导致循环的错误
    if len(numbers) == 0:
        return 0
    return sum(numbers) / len(numbers)

result = calculate_sum([])  # ZeroDivisionError
print(f"计算结果: {result}")