# scripts/create_base_dataset.py
"""
创建基础错误数据集
包含50个Python常见错误
"""

import json
from pathlib import Path

# Python常见错误模版
COMMON_ERRORS = [
    # ===== AtrributeError =====
    {
        "id":1,
        "category":"AttributeError",
        "difficulty":"easy",
        "error_type": "NoneType attribute access",
        "buggy_code": "user = None\nprint(user.name)",
        "error_message": "AttributeError: 'NoneType' object has no attribute 'name'",
        "fixed_code": "user = None\nif user is not None:\n    print(user.name)\nelse:\n    print('User is None')",
        "explanation": "尝试访问None对象的属性。需要先检查对象是否为None。",
        "solution_steps": [
            "添加None检查",
            "使用if语句保护属性访问",
            "或使用getattr()函数"
        ]
    },
    {
        "id": 2,
        "category": "AttributeError",
        "difficulty": "easy",
        "error_type": "Wrong attribute name",
        "buggy_code": "class User:\n    def __init__(self):\n        self.username = 'Alice'\n\nuser = User()\nprint(user.name)",
        "error_message": "AttributeError: 'User' object has no attribute 'name'",
        "fixed_code": "class User:\n    def __init__(self):\n        self.username = 'Alice'\n\nuser = User()\nprint(user.username)",
        "explanation": "属性名拼写错误。应该是username而不是name。",
        "solution_steps": [
            "检查属性名是否正确",
            "使用IDE的自动补全",
            "使用hasattr()检查属性是否存在"
        ]
    },
    
    # ===== TypeError =====
    {
        "id": 3,
        "category": "TypeError",
        "difficulty": "easy",
        "error_type": "String + Integer",
        "buggy_code": "age = 25\nmessage = 'I am ' + age + ' years old'",
        "error_message": "TypeError: can only concatenate str (not 'int') to str",
        "fixed_code": "age = 25\nmessage = 'I am ' + str(age) + ' years old'\n# 或使用f-string: message = f'I am {age} years old'",
        "explanation": "不能直接拼接字符串和整数。需要先转换类型。",
        "solution_steps": [
            "使用str()转换整数为字符串",
            "或使用f-string格式化",
            "或使用format()方法"
        ]
    },
    {
        "id": 4,
        "category": "TypeError",
        "difficulty": "easy",
        "error_type": "Unhashable type",
        "buggy_code": "my_dict = {[1, 2]: 'value'}",
        "error_message": "TypeError: unhashable type: 'list'",
        "fixed_code": "my_dict = {(1, 2): 'value'}  # 使用tuple代替list",
        "explanation": "字典的key必须是可哈希的类型。list不能作为key，应该使用tuple。",
        "solution_steps": [
            "将list改为tuple",
            "或使用不可变类型作为key",
            "理解可哈希类型的概念"
        ]
    },
    
    # ===== ValueError =====
    {
        "id": 5,
        "category": "ValueError",
        "difficulty": "easy",
        "error_type": "Invalid literal for int()",
        "buggy_code": "number = int('abc')",
        "error_message": "ValueError: invalid literal for int() with base 10: 'abc'",
        "fixed_code": "try:\n    number = int('abc')\nexcept ValueError:\n    print('Invalid number format')\n    number = 0",
        "explanation": "尝试将非数字字符串转换为整数。需要验证输入或捕获异常。",
        "solution_steps": [
            "使用try-except捕获ValueError",
            "验证字符串是否只包含数字",
            "使用isdigit()方法检查"
        ]
    },
    {
        "id": 6,
        "category": "ValueError",
        "difficulty": "easy",
        "error_type": "Too many values to unpack",
        "buggy_code": "a, b = [1, 2, 3]",
        "error_message": "ValueError: too many values to unpack (expected 2)",
        "fixed_code": "a, b, c = [1, 2, 3]\n# 或只取前两个: a, b = [1, 2, 3][:2]",
        "explanation": "解包时变量数量与值的数量不匹配。",
        "solution_steps": [
            "确保变量数量与值数量一致",
            "或使用*args接收多余的值",
            "检查数据结构"
        ]
    },
    
    # ===== IndexError =====
    {
        "id": 7,
        "category": "IndexError",
        "difficulty": "easy",
        "error_type": "List index out of range",
        "buggy_code": "numbers = [1, 2, 3]\nprint(numbers[5])",
        "error_message": "IndexError: list index out of range",
        "fixed_code": "numbers = [1, 2, 3]\nif len(numbers) > 5:\n    print(numbers[5])\nelse:\n    print('Index out of range')",
        "explanation": "访问的索引超出列表范围。需要检查列表长度。",
        "solution_steps": [
            "检查索引是否在有效范围内",
            "使用len()获取列表长度",
            "考虑使用get()方法（字典）"
        ]
    },
    
    # ===== KeyError =====
    {
        "id": 8,
        "category": "KeyError",
        "difficulty": "easy",
        "error_type": "Missing dictionary key",
        "buggy_code": "user = {'name': 'Alice'}\nprint(user['age'])",
        "error_message": "KeyError: 'age'",
        "fixed_code": "user = {'name': 'Alice'}\nprint(user.get('age', 'Unknown'))  # 使用get()提供默认值",
        "explanation": "访问字典中不存在的键。应该使用get()方法或先检查键是否存在。",
        "solution_steps": [
            "使用dict.get()方法",
            "提供默认值",
            "或使用in检查键是否存在"
        ]
    },
    
    # ===== NameError =====
    {
        "id": 9,
        "category": "NameError",
        "difficulty": "easy",
        "error_type": "Undefined variable",
        "buggy_code": "print(result)\nresult = 10",
        "error_message": "NameError: name 'result' is not defined",
        "fixed_code": "result = 10\nprint(result)",
        "explanation": "使用未定义的变量。必须先定义变量再使用。",
        "solution_steps": [
            "确保变量在使用前已定义",
            "检查变量名拼写",
            "注意变量作用域"
        ]
    },
    
    # ===== IndentationError =====
    {
        "id": 10,
        "category": "IndentationError",
        "difficulty": "easy",
        "error_type": "Unexpected indent",
        "buggy_code": "def greet():\nprint('Hello')",
        "error_message": "IndentationError: expected an indented block",
        "fixed_code": "def greet():\n    print('Hello')",
        "explanation": "Python使用缩进表示代码块。函数体必须缩进。",
        "solution_steps": [
            "为函数体添加缩进（4个空格）",
            "使用IDE自动格式化",
            "保持缩进一致性"
        ]
    },
]

def create_dataset():
    """创建完整数据集"""

    # 扩展到50个错误（后面可以继续添加）
    # TODO: 添加更多错误类型：
    # - ImportError
    # - FileNotFoundError  
    # - ZeroDivisionError
    # - RecursionError
    # - etc.

    dataset = {
        "metadata":{
            "version": "1.0",
            "total_errors": len(COMMON_ERRORS),
            "categories": list(set(e["category"] for e in COMMON_ERRORS)),
            "difficulty_levels": ["easy", "medium", "hard"]
        },
        "errors": COMMON_ERRORS
    }

    # 保存到文件
    output_path = Path("data/processed/python_errors_base.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 基础数据集创建完成")
    print(f"📁 保存路径: {output_path}")
    print(f"📊 错误数量: {len(COMMON_ERRORS)}")
    print(f"📂 错误类型: {dataset['metadata']['categories']}")
    
    return output_path


if __name__ == "__main__":
    create_dataset()