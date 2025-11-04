# scripts/create_base_dataset.py - 扩展版
"""
创建基础错误数据集
包含50个Python常见错误
"""

import json
from pathlib import Path

# Python常见错误模版（扩展到40个）
COMMON_ERRORS = [
    # ===== 你现有的10个保持不变 =====
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
    
    # ===== 新增30个案例 =====
    
    # AttributeError (再加2个)
    {
        "id": 11,
        "category": "AttributeError",
        "difficulty": "easy",
        "error_type": "List attribute error",
        "buggy_code": "items = [1, 2, 3]\nitems.add(4)",
        "error_message": "AttributeError: 'list' object has no attribute 'add'",
        "fixed_code": "items = [1, 2, 3]\nitems.append(4)  # list使用append而不是add",
        "explanation": "list对象没有add方法，应该使用append。",
        "solution_steps": [
            "使用append()添加单个元素",
            "使用extend()添加多个元素",
            "查看list的文档"
        ]
    },
    {
        "id": 12,
        "category": "AttributeError",
        "difficulty": "medium",
        "error_type": "String length",
        "buggy_code": "text = 'hello'\nprint(text.length)",
        "error_message": "AttributeError: 'str' object has no attribute 'length'",
        "fixed_code": "text = 'hello'\nprint(len(text))  # Python使用len()函数",
        "explanation": "Python字符串没有length属性，使用len()函数获取长度。",
        "solution_steps": [
            "使用len()函数",
            "记住Python的内置函数",
            "避免混淆其他语言的语法"
        ]
    },
    
    # TypeError (再加3个)
    {
        "id": 13,
        "category": "TypeError",
        "difficulty": "easy",
        "error_type": "Wrong argument count",
        "buggy_code": "def add(a, b):\n    return a + b\n\nresult = add(5)",
        "error_message": "TypeError: add() missing 1 required positional argument: 'b'",
        "fixed_code": "def add(a, b):\n    return a + b\n\nresult = add(5, 3)  # 提供两个参数",
        "explanation": "函数调用时参数数量不匹配。",
        "solution_steps": [
            "检查函数定义的参数数量",
            "提供所有必需参数",
            "或为参数设置默认值"
        ]
    },
    {
        "id": 14,
        "category": "TypeError",
        "difficulty": "medium",
        "error_type": "List indices must be integers",
        "buggy_code": "data = [10, 20, 30]\nprint(data[1.5])",
        "error_message": "TypeError: list indices must be integers or slices, not float",
        "fixed_code": "data = [10, 20, 30]\nprint(data[1])  # 使用整数索引",
        "explanation": "列表索引必须是整数，不能是浮点数。",
        "solution_steps": [
            "确保索引是整数类型",
            "必要时使用int()转换",
            "理解Python的索引规则"
        ]
    },
    {
        "id": 15,
        "category": "TypeError",
        "difficulty": "medium",
        "error_type": "Not callable",
        "buggy_code": "name = 'Alice'\nresult = name()",
        "error_message": "TypeError: 'str' object is not callable",
        "fixed_code": "# 字符串不能当函数调用\nname = 'Alice'\nprint(name)  # 直接使用变量",
        "explanation": "尝试调用一个不可调用的对象（字符串）。",
        "solution_steps": [
            "检查变量类型",
            "确认是否真的是函数",
            "可能是变量名冲突"
        ]
    },
    
    # ValueError (再加2个)
    {
        "id": 16,
        "category": "ValueError",
        "difficulty": "medium",
        "error_type": "Math domain error",
        "buggy_code": "import math\nresult = math.sqrt(-1)",
        "error_message": "ValueError: math domain error",
        "fixed_code": "import cmath\nresult = cmath.sqrt(-1)  # 使用cmath处理复数",
        "explanation": "math.sqrt()不能处理负数，需要使用cmath。",
        "solution_steps": [
            "使用cmath处理复数",
            "或先检查输入是否为正数",
            "理解数学函数的定义域"
        ]
    },
    {
        "id": 17,
        "category": "ValueError",
        "difficulty": "easy",
        "error_type": "Empty sequence",
        "buggy_code": "numbers = []\nmax_num = max(numbers)",
        "error_message": "ValueError: max() arg is an empty sequence",
        "fixed_code": "numbers = []\nif numbers:\n    max_num = max(numbers)\nelse:\n    max_num = None",
        "explanation": "max()函数不能作用于空序列。",
        "solution_steps": [
            "检查序列是否为空",
            "提供默认值",
            "使用try-except捕获异常"
        ]
    },
    
    # IndexError (再加2个)
    {
        "id": 18,
        "category": "IndexError",
        "difficulty": "easy",
        "error_type": "String index out of range",
        "buggy_code": "word = 'hi'\nprint(word[5])",
        "error_message": "IndexError: string index out of range",
        "fixed_code": "word = 'hi'\nif len(word) > 5:\n    print(word[5])\nelse:\n    print('Index out of range')",
        "explanation": "字符串索引超出范围。",
        "solution_steps": [
            "检查字符串长度",
            "使用负索引从末尾访问",
            "使用切片避免越界"
        ]
    },
    {
        "id": 19,
        "category": "IndexError",
        "difficulty": "medium",
        "error_type": "Pop from empty list",
        "buggy_code": "items = []\nitem = items.pop()",
        "error_message": "IndexError: pop from empty list",
        "fixed_code": "items = []\nif items:\n    item = items.pop()\nelse:\n    item = None",
        "explanation": "不能从空列表中pop元素。",
        "solution_steps": [
            "检查列表是否为空",
            "使用if语句保护",
            "或捕获IndexError异常"
        ]
    },
    
    # KeyError (再加2个)
    {
        "id": 20,
        "category": "KeyError",
        "difficulty": "easy",
        "error_type": "Nested dict key",
        "buggy_code": "data = {'user': {'name': 'Alice'}}\nage = data['user']['age']",
        "error_message": "KeyError: 'age'",
        "fixed_code": "data = {'user': {'name': 'Alice'}}\nage = data.get('user', {}).get('age', 'Unknown')",
        "explanation": "访问嵌套字典中不存在的键。",
        "solution_steps": [
            "使用链式get()方法",
            "每层都提供默认值",
            "或使用try-except"
        ]
    },
    {
        "id": 21,
        "category": "KeyError",
        "difficulty": "medium",
        "error_type": "Config missing",
        "buggy_code": "config = {'host': 'localhost'}\nport = config['port']",
        "error_message": "KeyError: 'port'",
        "fixed_code": "config = {'host': 'localhost'}\nport = config.get('port', 8080)  # 提供默认端口",
        "explanation": "配置文件缺少必需的键。",
        "solution_steps": [
            "使用get()提供合理默认值",
            "或在程序开始时验证配置",
            "记录缺少的配置项"
        ]
    },
    
    # NameError (再加2个)
    {
        "id": 22,
        "category": "NameError",
        "difficulty": "easy",
        "error_type": "Typo in variable name",
        "buggy_code": "count = 10\nprint(cont)",
        "error_message": "NameError: name 'cont' is not defined",
        "fixed_code": "count = 10\nprint(count)  # 修正拼写错误",
        "explanation": "变量名拼写错误。",
        "solution_steps": [
            "仔细检查变量名拼写",
            "使用IDE的自动补全",
            "保持命名一致性"
        ]
    },
    {
        "id": 23,
        "category": "NameError",
        "difficulty": "medium",
        "error_type": "Scope issue",
        "buggy_code": "def func():\n    x = 10\n\nfunc()\nprint(x)",
        "error_message": "NameError: name 'x' is not defined",
        "fixed_code": "def func():\n    x = 10\n    return x\n\nresult = func()\nprint(result)",
        "explanation": "变量作用域问题，局部变量在函数外不可见。",
        "solution_steps": [
            "理解变量作用域",
            "从函数返回需要的值",
            "或使用global关键字（不推荐）"
        ]
    },
    
    # ZeroDivisionError (3个)
    {
        "id": 24,
        "category": "ZeroDivisionError",
        "difficulty": "easy",
        "error_type": "Direct division by zero",
        "buggy_code": "result = 10 / 0",
        "error_message": "ZeroDivisionError: division by zero",
        "fixed_code": "divisor = 5  # 确保除数不为0\nif divisor != 0:\n    result = 10 / divisor",
        "explanation": "除数不能为零。",
        "solution_steps": [
            "在除法前检查除数",
            "使用if语句保护",
            "或捕获ZeroDivisionError异常"
        ]
    },
    {
        "id": 25,
        "category": "ZeroDivisionError",
        "difficulty": "medium",
        "error_type": "Empty list average",
        "buggy_code": "numbers = []\naverage = sum(numbers) / len(numbers)",
        "error_message": "ZeroDivisionError: division by zero",
        "fixed_code": "numbers = []\nif len(numbers) > 0:\n    average = sum(numbers) / len(numbers)\nelse:\n    average = 0",
        "explanation": "计算平均值时列表为空导致除零。",
        "solution_steps": [
            "检查列表是否为空",
            "提供默认值",
            "使用try-except处理"
        ]
    },
    {
        "id": 26,
        "category": "ZeroDivisionError",
        "difficulty": "medium",
        "error_type": "Modulo by zero",
        "buggy_code": "result = 10 % 0",
        "error_message": "ZeroDivisionError: integer division or modulo by zero",
        "fixed_code": "divisor = 3\nif divisor != 0:\n    result = 10 % divisor",
        "explanation": "取模运算的除数也不能为零。",
        "solution_steps": [
            "检查除数不为零",
            "与除法一样需要保护",
            "理解取模运算的含义"
        ]
    },
    
    # ImportError (3个)
    {
        "id": 27,
        "category": "ImportError",
        "difficulty": "easy",
        "error_type": "Module not found",
        "buggy_code": "import nonexistent_module",
        "error_message": "ModuleNotFoundError: No module named 'nonexistent_module'",
        "fixed_code": "# 安装模块: pip install module_name\n# 或检查拼写\nimport sys  # 使用标准库",
        "explanation": "尝试导入不存在的模块。",
        "solution_steps": [
            "检查模块名拼写",
            "使用pip安装缺失的包",
            "确认虚拟环境已激活"
        ]
    },
    {
        "id": 28,
        "category": "ImportError",
        "difficulty": "easy",
        "error_type": "Wrong import name",
        "buggy_code": "from os import nonexistent_func",
        "error_message": "ImportError: cannot import name 'nonexistent_func' from 'os'",
        "fixed_code": "from os import path  # 使用正确的函数名",
        "explanation": "模块中不存在指定的函数或类。",
        "solution_steps": [
            "查看模块文档",
            "使用dir()查看可用内容",
            "检查Python版本兼容性"
        ]
    },
    {
        "id": 29,
        "category": "ImportError",
        "difficulty": "medium",
        "error_type": "Circular import",
        "buggy_code": "# file1.py imports file2\n# file2.py imports file1\n# 导致循环导入",
        "error_message": "ImportError: cannot import name 'X' from partially initialized module",
        "fixed_code": "# 重构代码避免循环依赖\n# 或将导入移到函数内部",
        "explanation": "两个模块相互导入形成循环依赖。",
        "solution_steps": [
            "重构代码结构",
            "将共同依赖提取到第三个模块",
            "使用延迟导入"
        ]
    },
    
    # FileNotFoundError (3个)
    {
        "id": 30,
        "category": "FileNotFoundError",
        "difficulty": "easy",
        "error_type": "File not exist",
        "buggy_code": "with open('nonexistent.txt') as f:\n    content = f.read()",
        "error_message": "FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent.txt'",
        "fixed_code": "import os\nif os.path.exists('data.txt'):\n    with open('data.txt') as f:\n        content = f.read()\nelse:\n    print('File not found')",
        "explanation": "尝试打开不存在的文件。",
        "solution_steps": [
            "使用os.path.exists()检查文件",
            "捕获FileNotFoundError异常",
            "提供友好的错误提示"
        ]
    },
    {
        "id": 31,
        "category": "FileNotFoundError",
        "difficulty": "medium",
        "error_type": "Wrong path",
        "buggy_code": "with open('/wrong/path/file.txt') as f:\n    data = f.read()",
        "error_message": "FileNotFoundError: [Errno 2] No such file or directory",
        "fixed_code": "from pathlib import Path\nfile_path = Path('data/file.txt')\nif file_path.exists():\n    with open(file_path) as f:\n        data = f.read()",
        "explanation": "文件路径不正确。",
        "solution_steps": [
            "使用绝对路径或正确的相对路径",
            "使用pathlib处理路径",
            "打印路径进行调试"
        ]
    },
    {
        "id": 32,
        "category": "FileNotFoundError",
        "difficulty": "easy",
        "error_type": "Missing config file",
        "buggy_code": "import json\nwith open('config.json') as f:\n    config = json.load(f)",
        "error_message": "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'",
        "fixed_code": "import json\nimport os\n\nif os.path.exists('config.json'):\n    with open('config.json') as f:\n        config = json.load(f)\nelse:\n    config = {}  # 使用默认配置",
        "explanation": "配置文件不存在。",
        "solution_steps": [
            "提供默认配置",
            "创建配置文件模板",
            "给出清晰的错误提示"
        ]
    },
    
    # SyntaxError (3个)
    {
        "id": 33,
        "category": "SyntaxError",
        "difficulty": "easy",
        "error_type": "Missing colon",
        "buggy_code": "if x > 5\n    print('yes')",
        "error_message": "SyntaxError: invalid syntax",
        "fixed_code": "if x > 5:\n    print('yes')",
        "explanation": "if语句后缺少冒号。",
        "solution_steps": [
            "在if/for/while/def后添加冒号",
            "使用IDE自动检查语法",
            "养成良好的编码习惯"
        ]
    },
    {
        "id": 34,
        "category": "SyntaxError",
        "difficulty": "easy",
        "error_type": "Unclosed parenthesis",
        "buggy_code": "result = (1 + 2 * 3",
        "error_message": "SyntaxError: unexpected EOF while parsing",
        "fixed_code": "result = (1 + 2) * 3",
        "explanation": "括号未闭合。",
        "solution_steps": [
            "检查括号是否配对",
            "使用IDE的括号高亮",
            "注意括号嵌套"
        ]
    },
    {
        "id": 35,
        "category": "SyntaxError",
        "difficulty": "medium",
        "error_type": "Invalid print statement",
        "buggy_code": "print 'Hello'  # Python 2 语法",
        "error_message": "SyntaxError: Missing parentheses in call to 'print'",
        "fixed_code": "print('Hello')  # Python 3 语法",
        "explanation": "Python 3中print是函数，需要括号。",
        "solution_steps": [
            "使用Python 3语法",
            "print后加括号",
            "检查Python版本"
        ]
    },
    
    # UnboundLocalError (2个)
    {
        "id": 36,
        "category": "UnboundLocalError",
        "difficulty": "medium",
        "error_type": "Local variable referenced before assignment",
        "buggy_code": "x = 10\ndef func():\n    print(x)\n    x = 20\nfunc()",
        "error_message": "UnboundLocalError: local variable 'x' referenced before assignment",
        "fixed_code": "x = 10\ndef func():\n    global x\n    print(x)\n    x = 20\nfunc()",
        "explanation": "函数内部引用了局部变量但在使用前未赋值。",
        "solution_steps": [
            "使用global关键字",
            "或先赋值再使用",
            "理解变量作用域规则"
        ]
    },
    {
        "id": 37,
        "category": "UnboundLocalError",
        "difficulty": "medium",
        "error_type": "Counter increment",
        "buggy_code": "count = 0\ndef increment():\n    count += 1\nincrement()",
        "error_message": "UnboundLocalError: local variable 'count' referenced before assignment",
        "fixed_code": "count = 0\ndef increment():\n    global count\n    count += 1\nincrement()",
        "explanation": "尝试修改全局变量但未声明global。",
        "solution_steps": [
            "声明global变量",
            "或使用return返回新值",
            "考虑使用类封装状态"
        ]
    },
    
    # RecursionError (2个)
    {
        "id": 38,
        "category": "RecursionError",
        "difficulty": "medium",
        "error_type": "Missing base case",
        "buggy_code": "def factorial(n):\n    return n * factorial(n-1)\n\nfactorial(5)",
        "error_message": "RecursionError: maximum recursion depth exceeded",
        "fixed_code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n\nfactorial(5)",
        "explanation": "递归函数缺少基础情况（终止条件）。",
        "solution_steps": [
            "添加递归终止条件",
            "确保递归朝着终止条件前进",
            "考虑使用迭代代替递归"
        ]
    },
    {
        "id": 39,
        "category": "RecursionError",
        "difficulty": "hard",
        "error_type": "Infinite recursion",
        "buggy_code": "def count_down(n):\n    print(n)\n    count_down(n-1)\n\ncount_down(5)",
        "error_message": "RecursionError: maximum recursion depth exceeded",
        "fixed_code": "def count_down(n):\n    if n <= 0:\n        return\n    print(n)\n    count_down(n-1)\n\ncount_down(5)",
        "explanation": "递归永远不会停止。",
        "solution_steps": [
            "添加终止条件",
            "测试边界情况",
            "考虑使用循环"
        ]
    },
    
    # AssertionError (1个)
    {
        "id": 40,
        "category": "AssertionError",
        "difficulty": "easy",
        "error_type": "Failed assertion",
        "buggy_code": "x = 5\nassert x > 10, 'x must be greater than 10'",
        "error_message": "AssertionError: x must be greater than 10",
        "fixed_code": "x = 5\nif x <= 10:\n    raise ValueError('x must be greater than 10')\n# 或修改断言条件: assert x > 0",
        "explanation": "断言条件不满足。",
        "solution_steps": [
            "检查断言条件是否合理",
            "提供清晰的断言消息",
            "考虑使用显式的异常处理"
        ]
    }
]

def create_dataset():
    """创建完整数据集"""
    
    dataset = {
        "metadata": {
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
    print(f"📂 错误类型: {sorted(set(e['category'] for e in COMMON_ERRORS))}")
    
    # 统计
    category_count = {}
    difficulty_count = {}
    for error in COMMON_ERRORS:
        cat = error['category']
        diff = error['difficulty']
        category_count[cat] = category_count.get(cat, 0) + 1
        difficulty_count[diff] = difficulty_count.get(diff, 0) + 1
    
    print("\n📊 按类别分布:")
    for cat, count in sorted(category_count.items()):
        print(f"  {cat}: {count}")
    
    print("\n📊 按难度分布:")
    for diff, count in sorted(difficulty_count.items()):
        print(f"  {diff}: {count}")
    
    return output_path


if __name__ == "__main__":
    create_dataset()