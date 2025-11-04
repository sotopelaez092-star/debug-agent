# scripts/create_simple_cases.py
"""快速生成28个简单但有代表性的测试案例"""

SIMPLE_CASES = [
    # AttributeError (3个)
    {
        "code": "x = None\nprint(x.value)",
        "error": "AttributeError: 'NoneType' object has no attribute 'value'",
        "fix": "if x is not None:\n    print(x.value)",
        "difficulty": "easy"
    },
    {
        "code": "lst = [1, 2, 3]\nlst.add(4)",  
        "error": "AttributeError: 'list' object has no attribute 'add'",
        "fix": "lst.append(4)",
        "difficulty": "easy"
    },
    {
        "code": "s = 'hello'\nprint(s.length)",
        "error": "AttributeError: 'str' object has no attribute 'length'",
        "fix": "print(len(s))",
        "difficulty": "easy"
    },
    
    # TypeError (3个)
    {
        "code": "result = '5' + 3",
        "error": "TypeError: can only concatenate str (not 'int') to str",
        "fix": "result = int('5') + 3",
        "difficulty": "easy"
    },
    {
        "code": "nums = [1, 2, 3]\nprint(nums[1.5])",
        "error": "TypeError: list indices must be integers or slices, not float",
        "fix": "print(nums[1])",
        "difficulty": "easy"
    },
    {
        "code": "def func(a, b):\n    return a + b\nfunc(1)",
        "error": "TypeError: func() missing 1 required positional argument: 'b'",
        "fix": "func(1, 2)",
        "difficulty": "easy"
    },
    
    # IndexError (2个)
    {
        "code": "lst = [1, 2, 3]\nprint(lst[5])",
        "error": "IndexError: list index out of range",
        "fix": "if len(lst) > 5:\n    print(lst[5])",
        "difficulty": "easy"
    },
    {
        "code": "s = 'hello'\nprint(s[10])",
        "error": "IndexError: string index out of range",
        "fix": "if len(s) > 10:\n    print(s[10])",
        "difficulty": "easy"
    },
    
    # KeyError (2个)
    {
        "code": "d = {'a': 1}\nprint(d['b'])",
        "error": "KeyError: 'b'",
        "fix": "print(d.get('b', 'default'))",
        "difficulty": "easy"
    },
    {
        "code": "config = {'host': 'localhost'}\nport = config['port']",
        "error": "KeyError: 'port'",
        "fix": "port = config.get('port', 8080)",
        "difficulty": "easy"
    },
    
    # ValueError (3个)
    {
        "code": "num = int('abc')",
        "error": "ValueError: invalid literal for int() with base 10: 'abc'",
        "fix": "try:\n    num = int('abc')\nexcept ValueError:\n    num = 0",
        "difficulty": "easy"
    },
    {
        "code": "a, b = [1, 2, 3]",
        "error": "ValueError: too many values to unpack (expected 2)",
        "fix": "a, b, c = [1, 2, 3]",
        "difficulty": "easy"
    },
    {
        "code": "import math\nmath.sqrt(-1)",
        "error": "ValueError: math domain error",
        "fix": "import cmath\ncmath.sqrt(-1)",
        "difficulty": "medium"
    },
    
    # NameError (2个)
    {
        "code": "print(undefined_var)",
        "error": "NameError: name 'undefined_var' is not defined",
        "fix": "undefined_var = 'value'\nprint(undefined_var)",
        "difficulty": "easy"
    },
    {
        "code": "def func():\n    return x\nfunc()",
        "error": "NameError: name 'x' is not defined",
        "fix": "def func():\n    x = 10\n    return x",
        "difficulty": "easy"
    },
    
    # ZeroDivisionError (2个)
    {
        "code": "result = 10 / 0",
        "error": "ZeroDivisionError: division by zero",
        "fix": "if denominator != 0:\n    result = 10 / denominator",
        "difficulty": "easy"
    },
    {
        "code": "nums = [1, 2, 3]\navg = sum(nums) / len(nums[5:])",
        "error": "ZeroDivisionError: division by zero",
        "fix": "subset = nums[5:]\nif len(subset) > 0:\n    avg = sum(subset) / len(subset)",
        "difficulty": "medium"
    },
    
    # ImportError (2个)
    {
        "code": "import nonexistent_module",
        "error": "ModuleNotFoundError: No module named 'nonexistent_module'",
        "fix": "# pip install nonexistent_module",
        "difficulty": "easy"
    },
    {
        "code": "from os import nonexistent_func",
        "error": "ImportError: cannot import name 'nonexistent_func' from 'os'",
        "fix": "from os import path",
        "difficulty": "easy"
    },
    
    # FileNotFoundError (2个)
    {
        "code": "with open('nonexistent.txt') as f:\n    content = f.read()",
        "error": "FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent.txt'",
        "fix": "import os\nif os.path.exists('file.txt'):\n    with open('file.txt') as f:\n        content = f.read()",
        "difficulty": "easy"
    },
    {
        "code": "import json\nwith open('config.json') as f:\n    data = json.load(f)",
        "error": "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'",
        "fix": "import os\nif os.path.exists('config.json'):\n    with open('config.json') as f:\n        data = json.load(f)\nelse:\n    data = {}",
        "difficulty": "easy"
    },
    
    # IndentationError (2个)
    {
        "code": "def func():\nreturn 1",
        "error": "IndentationError: expected an indented block",
        "fix": "def func():\n    return 1",
        "difficulty": "easy"
    },
    {
        "code": "if True:\nprint('yes')",
        "error": "IndentationError: expected an indented block",
        "fix": "if True:\n    print('yes')",
        "difficulty": "easy"
    },
    
    # UnboundLocalError (2个)
    {
        "code": "x = 10\ndef func():\n    print(x)\n    x = 20\nfunc()",
        "error": "UnboundLocalError: local variable 'x' referenced before assignment",
        "fix": "x = 10\ndef func():\n    global x\n    print(x)\n    x = 20",
        "difficulty": "medium"
    },
    {
        "code": "count = 0\ndef increment():\n    count += 1\nincrement()",
        "error": "UnboundLocalError: local variable 'count' referenced before assignment",
        "fix": "count = 0\ndef increment():\n    global count\n    count += 1",
        "difficulty": "medium"
    },
    
    # RecursionError (1个)
    {
        "code": "def factorial(n):\n    return n * factorial(n-1)\nfactorial(5)",
        "error": "RecursionError: maximum recursion depth exceeded",
        "fix": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
        "difficulty": "medium"
    },
    
    # AssertionError (1个)  
    {
        "code": "x = 5\nassert x > 10",
        "error": "AssertionError",
        "fix": "x = 5\nassert x > 0, 'x must be positive'",
        "difficulty": "easy"
    },
]

# 生成完整的测试用例
import json

test_cases = []
for i, case in enumerate(SIMPLE_CASES, start=23):  # 从23开始编号
    test_cases.append({
        "id": i,
        "code": case["code"],
        "error": case["error"],
        "ground_truth": case["fix"],
        "difficulty": case["difficulty"],
        "source": "manual"
    })

# 保存
with open('data/test_cases/additional_28.json', 'w') as f:
    json.dump(test_cases, f, indent=2, ensure_ascii=False)

print(f"✅ 生成了 {len(test_cases)} 个补充案例")