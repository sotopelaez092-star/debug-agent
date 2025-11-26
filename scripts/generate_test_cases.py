"""批量生成测试案例"""
import json
import os


# ============================================================
# 单文件错误模板
# ============================================================

SINGLE_FILE_TEMPLATES = {
    # NameError（5个）
    'NameError_spelling_1': {
        'name': 'NameError - 变量拼写错误',
        'category': '单文件',
        'error_type': 'NameError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "def greet(name):\n    print(f'Hello, {nme}')\n\ngreet('Tom')"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'nme' is not defined",
        'expected_fix_type': '拼写纠正',
        'notes': 'nme → name'
    },
    
    'NameError_undefined_var': {
        'name': 'NameError - 变量未定义',
        'category': '单文件',
        'error_type': 'NameError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "x = 10\nprint(y)"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'y' is not defined",
        'expected_fix_type': '定义变量或纠正名称',
        'notes': 'y未定义'
    },
    
    'NameError_function_typo': {
        'name': 'NameError - 函数名拼写错误',
        'category': '单文件',
        'error_type': 'NameError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "def calculate(a, b):\n    return a + b\n\nresult = calculte(5, 3)\nprint(result)"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'calculte' is not defined",
        'expected_fix_type': '函数名纠正',
        'notes': 'calculte → calculate'
    },
    
    'NameError_scope': {
        'name': 'NameError - 作用域问题',
        'category': '单文件',
        'error_type': 'NameError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "def foo():\n    x = 10\n\nfoo()\nprint(x)"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'x' is not defined",
        'expected_fix_type': '返回变量或全局变量',
        'notes': 'x在函数作用域内'
    },
    
    'NameError_before_assignment': {
        'name': 'NameError - 使用前未赋值',
        'category': '单文件',
        'error_type': 'NameError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "print(total)\ntotal = 0"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'total' is not defined",
        'expected_fix_type': '调整语句顺序',
        'notes': '先使用后定义'
    },
    
    # TypeError（3个）
    'TypeError_string_int': {
        'name': 'TypeError - 字符串和整数相加',
        'category': '单文件',
        'error_type': 'TypeError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "result = '5' + 3\nprint(result)"
        },
        'error_file': 'main.py',
        'error_message': "TypeError: can only concatenate str (not 'int') to str",
        'expected_fix_type': '类型转换',
        'notes': '需要int() 或 str()'
    },
    
    'TypeError_missing_arg': {
        'name': 'TypeError - 缺少参数',
        'category': '单文件',
        'error_type': 'TypeError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "def add(a, b):\n    return a + b\n\nresult = add(5)\nprint(result)"
        },
        'error_file': 'main.py',
        'error_message': "TypeError: add() missing 1 required positional argument: 'b'",
        'expected_fix_type': '添加参数',
        'notes': '缺少参数b'
    },
    
    'TypeError_unhashable': {
        'name': 'TypeError - 不可哈希类型作为字典key',
        'category': '单文件',
        'error_type': 'TypeError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "d = {[1, 2]: 'value'}\nprint(d)"
        },
        'error_file': 'main.py',
        'error_message': "TypeError: unhashable type: 'list'",
        'expected_fix_type': '改用tuple',
        'notes': 'list不能作为字典key'
    },
    
    # AttributeError（3个）
    'AttributeError_none': {
        'name': 'AttributeError - None对象',
        'category': '单文件',
        'error_type': 'AttributeError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "user = None\nprint(user.name)"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'NoneType' object has no attribute 'name'",
        'expected_fix_type': '添加None检查',
        'notes': 'None对象没有属性'
    },
    
    'AttributeError_wrong_attr': {
        'name': 'AttributeError - 错误的属性名',
        'category': '单文件',
        'error_type': 'AttributeError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "s = 'hello'\nprint(s.uppper())"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'str' object has no attribute 'uppper'",
        'expected_fix_type': '纠正方法名',
        'notes': 'uppper → upper'
    },
    
    'AttributeError_list': {
        'name': 'AttributeError - 列表没有该方法',
        'category': '单文件',
        'error_type': 'AttributeError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "numbers = [1, 2, 3]\nresult = numbers.add(4)\nprint(result)"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'list' object has no attribute 'add'",
        'expected_fix_type': '改用append',
        'notes': 'list用append不是add'
    },
    
    # KeyError（2个）
    'KeyError_missing_key': {
        'name': 'KeyError - 字典key不存在',
        'category': '单文件',
        'error_type': 'KeyError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "user = {'name': 'Tom'}\nprint(user['age'])"
        },
        'error_file': 'main.py',
        'error_message': "KeyError: 'age'",
        'expected_fix_type': '使用get()或添加key',
        'notes': 'age键不存在'
    },
    
    'KeyError_typo': {
        'name': 'KeyError - key拼写错误',
        'category': '单文件',
        'error_type': 'KeyError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "data = {'count': 10}\nprint(data['cont'])"
        },
        'error_file': 'main.py',
        'error_message': "KeyError: 'cont'",
        'expected_fix_type': '纠正key名',
        'notes': 'cont → count'
    },
    
    # IndexError（2个）
    'IndexError_list': {
        'name': 'IndexError - 列表索引越界',
        'category': '单文件',
        'error_type': 'IndexError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "numbers = [1, 2, 3]\nprint(numbers[5])"
        },
        'error_file': 'main.py',
        'error_message': "IndexError: list index out of range",
        'expected_fix_type': '检查索引范围',
        'notes': '索引5超出范围'
    },
    
    'IndexError_empty': {
        'name': 'IndexError - 空列表访问',
        'category': '单文件',
        'error_type': 'IndexError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "items = []\nfirst = items[0]\nprint(first)"
        },
        'error_file': 'main.py',
        'error_message': "IndexError: list index out of range",
        'expected_fix_type': '检查列表是否为空',
        'notes': '空列表无法访问'
    },
}

# ============================================================
# 跨文件错误模板
# ============================================================

CROSS_FILE_TEMPLATES = {
    # NameError跨文件（4个）
    'CrossFile_NameError_function': {
        'name': 'NameError - 跨文件函数未import',
        'category': '跨文件',
        'error_type': 'NameError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "result = calculate(10, 20)\nprint(f'Result: {result}')",
            'utils.py': "def calculate(a, b):\n    return a + b"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'calculate' is not defined",
        'expected_fix_type': '添加import',
        'notes': '需要from utils import calculate'
    },
    
    'CrossFile_NameError_class': {
        'name': 'NameError - 跨文件类未import',
        'category': '跨文件',
        'error_type': 'NameError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "user = User('Tom')\nprint(user.name)",
            'models.py': "class User:\n    def __init__(self, name):\n        self.name = name"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'User' is not defined",
        'expected_fix_type': '添加import',
        'notes': '需要from models import User'
    },
    
    'CrossFile_NameError_multiple': {
        'name': 'NameError - 多个函数未import',
        'category': '跨文件',
        'error_type': 'NameError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "x = add(5, 3)\ny = multiply(4, 2)\nprint(x, y)",
            'utils.py': "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'add' is not defined",
        'expected_fix_type': '添加多个import',
        'notes': '需要from utils import add, multiply'
    },
    
    'CrossFile_NameError_subdirectory': {
        'name': 'NameError - 子目录模块未import',
        'category': '跨文件',
        'error_type': 'NameError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "result = multiply(3, 4)\nprint(result)",
            'src/math_utils.py': "def multiply(a, b):\n    return a * b"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'multiply' is not defined",
        'expected_fix_type': '添加子目录import',
        'notes': '需要from src.math_utils import multiply'
    },
    
    # ImportError（3个）
    'CrossFile_ImportError_module': {
        'name': 'ImportError - 模块名拼写错误',
        'category': '跨文件',
        'error_type': 'ImportError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "from utls import calculate\nresult = calculate(5, 3)\nprint(result)",
            'utils.py': "def calculate(a, b):\n    return a + b"
        },
        'error_file': 'main.py',
        'error_message': "ModuleNotFoundError: No module named 'utls'",
        'expected_fix_type': '纠正模块名',
        'notes': 'utls → utils'
    },
    
    'CrossFile_ImportError_function': {
        'name': 'ImportError - 函数名错误',
        'category': '跨文件',
        'error_type': 'ImportError',
        'difficulty': '简单',
        'project_files': {
            'main.py': "from utils import calcuate\nresult = calcuate(5, 3)\nprint(result)",
            'utils.py': "def calculate(a, b):\n    return a + b"
        },
        'error_file': 'main.py',
        'error_message': "ImportError: cannot import name 'calcuate' from 'utils'",
        'expected_fix_type': '纠正函数名',
        'notes': 'calcuate → calculate'
    },
    
    'CrossFile_ImportError_subdirectory': {
        'name': 'ImportError - 子目录路径错误',
        'category': '跨文件',
        'error_type': 'ImportError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "from math_utils import multiply\nresult = multiply(3, 4)\nprint(result)",
            'src/math_utils.py': "def multiply(a, b):\n    return a * b"
        },
        'error_file': 'main.py',
        'error_message': "ModuleNotFoundError: No module named 'math_utils'",
        'expected_fix_type': '添加路径前缀',
        'notes': '需要from src.math_utils'
    },
    
    # AttributeError跨文件（3个）
    'CrossFile_AttributeError_class': {
        'name': 'AttributeError - 跨文件类属性错误',
        'category': '跨文件',
        'error_type': 'AttributeError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "from models import User\nuser = User('Tom')\nprint(user.age)",
            'models.py': "class User:\n    def __init__(self, name):\n        self.name = name"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'User' object has no attribute 'age'",
        'expected_fix_type': '添加属性或检查',
        'notes': 'User没有age属性'
    },
    
    'CrossFile_AttributeError_method': {
        'name': 'AttributeError - 跨文件方法名错误',
        'category': '跨文件',
        'error_type': 'AttributeError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "from calculator import Calculator\ncalc = Calculator()\nresult = calc.add(5, 3)\nprint(result)",
            'calculator.py': "class Calculator:\n    def sum(self, a, b):\n        return a + b"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'Calculator' object has no attribute 'add'",
        'expected_fix_type': '纠正方法名',
        'notes': 'add → sum'
    },
    
    'CrossFile_AttributeError_import': {
        'name': 'AttributeError - import路径错误',
        'category': '跨文件',
        'error_type': 'AttributeError',
        'difficulty': '中等',
        'project_files': {
            'main.py': "import utils\nresult = utils.calculte(5, 3)\nprint(result)",
            'utils.py': "def calculate(a, b):\n    return a + b"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: module 'utils' has no attribute 'calculte'",
        'expected_fix_type': '纠正函数名',
        'notes': 'calculte → calculate'
    },
}

# ============================================================
# 复杂场景模板
# ============================================================

COMPLEX_TEMPLATES = {
    'Complex_nested_import': {
        'name': '复杂 - 多层嵌套import',
        'category': '复杂',
        'error_type': 'NameError',
        'difficulty': '复杂',
        'project_files': {
            'main.py': "result = process_data([1, 2, 3])\nprint(result)",
            'processor.py': "from utils.math_utils import calculate\n\ndef process_data(data):\n    return calculate(sum(data), len(data))",
            'utils/math_utils.py': "def calculate(total, count):\n    return total / count if count > 0 else 0"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'process_data' is not defined",
        'expected_fix_type': '多层import',
        'notes': '需要from processor import process_data'
    },
    
    'Complex_multiple_errors': {
        'name': '复杂 - 同一文件多个错误',
        'category': '复杂',
        'error_type': 'NameError',
        'difficulty': '复杂',
        'project_files': {
            'main.py': "x = add(5, 3)\ny = multiply(x, 2)\nz = divde(y, 4)\nprint(z)",
            'utils.py': "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n\ndef divide(a, b):\n    return a / b"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'add' is not defined",
        'expected_fix_type': 'import + 拼写纠正',
        'notes': '需要import且divde → divide'
    },
    
    'Complex_circular_logic': {
        'name': '复杂 - 逻辑错误+类型错误',
        'category': '复杂',
        'error_type': 'TypeError',
        'difficulty': '复杂',
        'project_files': {
            'main.py': "from calculator import average\nnumbers = ['1', '2', '3']\nresult = average(numbers)\nprint(f'Average: {result}')",
            'calculator.py': "def average(numbers):\n    return sum(numbers) / len(numbers)"
        },
        'error_file': 'main.py',
        'error_message': "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        'expected_fix_type': '类型转换',
        'notes': '字符串列表需要转换为整数'
    },
    
    'Complex_deep_subdirectory': {
        'name': '复杂 - 深层子目录',
        'category': '复杂',
        'error_type': 'NameError',
        'difficulty': '复杂',
        'project_files': {
            'main.py': "result = format_data(data)\nprint(result)",
            'src/utils/formatters/text.py': "def format_data(data):\n    return str(data).upper()"
        },
        'error_file': 'main.py',
        'error_message': "NameError: name 'format_data' is not defined",
        'expected_fix_type': '深层import',
        'notes': '需要from src.utils.formatters.text import format_data'
    },
    
    'Complex_mixed_errors': {
        'name': '复杂 - 混合错误类型',
        'category': '复杂',
        'error_type': 'Multiple',
        'difficulty': '复杂',
        'project_files': {
            'main.py': "from utils import process\ndata = None\nresult = process(data)\nprint(result.upper())",
            'utils.py': "def process(data):\n    if data is None:\n        return None\n    return data * 2"
        },
        'error_file': 'main.py',
        'error_message': "AttributeError: 'NoneType' object has no attribute 'upper'",
        'expected_fix_type': 'None检查',
        'notes': 'process返回None，需要检查'
    },
}


def generate_test_cases():
    """生成所有测试案例"""
    test_cases = []
    test_id = 1
    
    # 生成单文件错误（15个）
    for key, template in SINGLE_FILE_TEMPLATES.items():
        test_case = {
            'id': test_id,
            **template
        }
        test_cases.append(test_case)
        test_id += 1
    
    # 生成跨文件错误（10个）
    for key, template in CROSS_FILE_TEMPLATES.items():
        test_case = {
            'id': test_id,
            **template
        }
        test_cases.append(test_case)
        test_id += 1
    
    # 生成复杂场景（5个）
    for key, template in COMPLEX_TEMPLATES.items():
        test_case = {
            'id': test_id,
            **template
        }
        test_cases.append(test_case)
        test_id += 1
    
    return {'test_cases': test_cases}


def main():
    """主函数"""
    print("=" * 60)
    print("生成测试案例...")
    print("=" * 60)
    
    # 生成测试案例
    data = generate_test_cases()
    
    # 统计
    total = len(data['test_cases'])
    categories = {}
    error_types = {}
    
    for case in data['test_cases']:
        # 统计类别
        cat = case['category']
        categories[cat] = categories.get(cat, 0) + 1
        
        # 统计错误类型
        err = case['error_type']
        error_types[err] = error_types.get(err, 0) + 1
    
    print(f"\n总计: {total}个测试案例")
    print(f"\n按类别:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}个")
    
    print(f"\n按错误类型:")
    for err, count in error_types.items():
        print(f"  - {err}: {count}个")
    
    # 保存
    output_dir = 'data/test_cases'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'week6_test_set.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 已保存到: {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()