"""
单文件测试案例集合

包含10个测试案例，覆盖常见的Python错误类型：
- 简单级别(5个): NameError, TypeError, AttributeError, ZeroDivisionError, IndexError
- 中等级别(3个): KeyError, ValueError, 边界条件
- 困难级别(2个): 逻辑错误, 多重错误

每个案例包含：
- id: 唯一标识
- name: 案例名称  
- difficulty: 难度（easy/medium/hard）
- buggy_code: 包含错误的代码
- error_traceback: 错误的traceback信息
- expected_fix_type: 预期修复类型
- description: 案例描述
"""

from typing import List, Dict, Any


TEST_CASES: List[Dict[str, Any]] = [
    # ============ 简单级别 (5个) ============
    
    {
        "id": "TC001",
        "name": "NameError - 变量拼写错误",
        "difficulty": "easy",
        "buggy_code": """def greet(name):
    message = f"Hello, {nme}!"
    return message

result = greet("Alice")
print(result)
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 4, in <module>
    result = greet("Alice")
  File "test.py", line 2, in greet
    message = f"Hello, {nme}!"
NameError: name 'nme' is not defined
""",
        "expected_fix_type": "变量名更正",
        "description": "函数参数名为name，但在f-string中拼写成nme"
    },
    
    {
        "id": "TC002", 
        "name": "TypeError - 字符串和数字相加",
        "difficulty": "easy",
        "buggy_code": """def calculate_total(quantity, price):
    total = quantity + price
    return total

result = calculate_total("5", 10)
print(f"Total: {result}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 4, in <module>
    result = calculate_total("5", 10)
  File "test.py", line 2, in calculate_total
    total = quantity + price
TypeError: can only concatenate str (not "int") to str
""",
        "expected_fix_type": "类型转换",
        "description": "字符串quantity和整数price相加，需要类型转换"
    },
    
    {
        "id": "TC003",
        "name": "AttributeError - NoneType访问属性", 
        "difficulty": "easy",
        "buggy_code": """def get_user():
    # 模拟数据库查询，用户不存在返回None
    return None

def print_user_name():
    user = get_user()
    print(f"User name: {user.name}")

print_user_name()
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 9, in <module>
    print_user_name()
  File "test.py", line 7, in print_user_name
    print(f"User name: {user.name}")
AttributeError: 'NoneType' object has no attribute 'name'
""",
        "expected_fix_type": "None检查",
        "description": "get_user返回None，但直接访问.name属性"
    },
    
    {
        "id": "TC004",
        "name": "ZeroDivisionError - 除零错误",
        "difficulty": "easy", 
        "buggy_code": """def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    return average

result = calculate_average([])
print(f"Average: {result}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 7, in <module>
    result = calculate_average([])
  File "test.py", line 4, in calculate_average
    average = total / count
ZeroDivisionError: division by zero
""",
        "expected_fix_type": "空列表检查",
        "description": "空列表导致len()为0，除法出错"
    },
    
    {
        "id": "TC005",
        "name": "IndexError - 列表索引越界",
        "difficulty": "easy",
        "buggy_code": """def get_first_and_last(items):
    first = items[0]
    last = items[-1]
    return first, last

result = get_first_and_last([])
print(f"First: {result[0]}, Last: {result[1]}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 6, in <module>
    result = get_first_and_last([])
  File "test.py", line 2, in get_first_and_last
    first = items[0]
IndexError: list index out of range
""",
        "expected_fix_type": "长度检查",
        "description": "空列表访问索引0导致越界"
    },
    
    # ============ 中等级别 (3个) ============
    
    {
        "id": "TC006",
        "name": "KeyError - 字典key不存在",
        "difficulty": "medium",
        "buggy_code": """def get_user_info(user_data):
    name = user_data['name']
    age = user_data['age']
    email = user_data['email']
    return f"{name} ({age}) - {email}"

user = {'name': 'Alice', 'email': 'alice@example.com'}
info = get_user_info(user)
print(info)
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 8, in <module>
    info = get_user_info(user)
  File "test.py", line 3, in get_user_info
    age = user_data['age']
KeyError: 'age'
""",
        "expected_fix_type": "字典key检查",
        "description": "字典中缺少'age'键，直接访问导致KeyError"
    },
    
    {
        "id": "TC007",
        "name": "ValueError - 类型转换失败",
        "difficulty": "medium",
        "buggy_code": """def parse_age(age_string):
    age = int(age_string)
    return age

def check_adult(age_input):
    age = parse_age(age_input)
    return age >= 18

result = check_adult("twenty")
print(f"Is adult: {result}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 9, in <module>
    result = check_adult("twenty")
  File "test.py", line 6, in check_adult
    age = parse_age(age_input)
  File "test.py", line 2, in parse_age
    age = int(age_string)
ValueError: invalid literal for int() with base 10: 'twenty'
""",
        "expected_fix_type": "输入验证或异常处理",
        "description": "尝试将非数字字符串转换为整数"
    },
    
    {
        "id": "TC008",
        "name": "ValueError - 空序列的max/min",
        "difficulty": "medium",
        "buggy_code": """def find_maximum(numbers):
    maximum = max(numbers)
    return maximum

def find_minimum(numbers):
    minimum = min(numbers)
    return minimum

result_max = find_maximum([])
result_min = find_minimum([])
print(f"Max: {result_max}, Min: {result_min}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 9, in <module>
    result_max = find_maximum([])
  File "test.py", line 2, in find_maximum
    maximum = max(numbers)
ValueError: max() arg is an empty sequence
""",
        "expected_fix_type": "空列表检查",
        "description": "对空列表调用max()函数导致ValueError"
    },
    
    # ============ 困难级别 (2个) ============
    
    {
        "id": "TC009",
        "name": "逻辑错误 - 闰年判断错误",
        "difficulty": "hard",
        "buggy_code": """def is_leap_year(year):
    # 错误的闰年判断逻辑
    return year % 4 == 0

# 测试
test_years = [2000, 1900, 2004, 2100]
for year in test_years:
    result = is_leap_year(year)
    print(f"{year}: {result}")

# 期望：2000=True, 1900=False, 2004=True, 2100=False
# 实际：2000=True, 1900=True, 2004=True, 2100=True
# 1900和2100的结果错误
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 7, in <module>
    result = is_leap_year(year)
  File "test.py", line 3, in is_leap_year
    return year % 4 == 0
AssertionError: 闰年判断逻辑错误
预期: is_leap_year(1900) = False
实际: is_leap_year(1900) = True
说明: 遗漏了能被100整除但不能被400整除的情况
""",
        "expected_fix_type": "逻辑修正",
        "description": "闰年判断逻辑不完整，遗漏了100和400的规则"
    },
    
    {
        "id": "TC010",
        "name": "多重错误 - 文件操作+字典+类型",
        "difficulty": "hard",
        "buggy_code": """import json

def load_user_data(user_id):
    filename = f"user_{user_id}.jsn"
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def calculate_discount(user_id):
    user = load_user_data(user_id)
    age = user['age']
    if age > 60:
        return 0.2
    elif age > 18:
        return 0.1
    else:
        return 0

discount = calculate_discount(1)
print(f"Discount: {discount}")
""",
        "error_traceback": """Traceback (most recent call last):
  File "test.py", line 19, in <module>
    discount = calculate_discount(1)
  File "test.py", line 11, in calculate_discount
    user = load_user_data(user_id)
  File "test.py", line 5, in load_user_data
    with open(filename, 'r') as f:
FileNotFoundError: [Errno 2] No such file or directory: 'user_1.jsn'
""",
        "expected_fix_type": "多重修复",
        "description": """包含3个错误：
1. 文件扩展名错误(.jsn应为.json)
2. 缺少文件存在性检查
3. 缺少字典key检查和类型验证(age可能不存在或为字符串)"""
    }
]


def get_test_case_by_id(test_id: str) -> Dict[str, Any]:
    """
    根据ID获取测试案例
    
    Args:
        test_id: 测试案例ID (如'TC001')
        
    Returns:
        测试案例字典
        
    Raises:
        ValueError: 如果ID不存在
    """
    for case in TEST_CASES:
        if case['id'] == test_id:
            return case
    raise ValueError(f"测试案例 {test_id} 不存在")


def get_test_cases_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """
    根据难度获取测试案例列表
    
    Args:
        difficulty: 难度级别 ('easy', 'medium', 'hard')
        
    Returns:
        测试案例列表
    """
    return [case for case in TEST_CASES if case['difficulty'] == difficulty]


def print_test_cases_summary():
    """打印测试案例摘要"""
    print("=" * 60)
    print("测试案例总览")
    print("=" * 60)
    
    by_difficulty = {
        'easy': get_test_cases_by_difficulty('easy'),
        'medium': get_test_cases_by_difficulty('medium'),
        'hard': get_test_cases_by_difficulty('hard')
    }
    
    for difficulty, cases in by_difficulty.items():
        print(f"\n{difficulty.upper()} ({len(cases)}个):")
        for case in cases:
            print(f"  - {case['id']}: {case['name']}")
    
    print(f"\n总计: {len(TEST_CASES)}个测试案例")
    print("=" * 60)


if __name__ == "__main__":
    print_test_cases_summary()