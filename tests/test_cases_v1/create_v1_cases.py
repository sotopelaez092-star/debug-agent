#!/usr/bin/env python3
"""创建 V1-style 简单拼写错误测试用例"""
import json
import os
from pathlib import Path

def create_test_case(base_dir, case_info):
    """创建一个测试用例"""
    case_dir = base_dir / case_info['case_id']
    case_dir.mkdir(exist_ok=True)
    
    # 写入 main.py
    (case_dir / 'main.py').write_text(case_info['main_code'])
    
    # 写入其他文件
    for filename, content in case_info.get('extra_files', {}).items():
        (case_dir / filename).write_text(content)
    
    # 写入 metadata.json
    metadata = {
        'error_type': case_info['error_type'],
        'case_id': case_info['case_id'],
        'description': case_info['description'],
        'error_file': case_info.get('error_file', 'main.py'),
        'error_message': case_info['error_message'],
        'expected_fix': case_info['expected_fix'],
        'difficulty': case_info.get('difficulty', 'easy'),
        'requires_exploration': False,
        'edit_distance': case_info['edit_distance'],
        'expected_similarity': case_info['expected_similarity']
    }
    
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Created: {case_info['case_id']}")

# 测试用例定义
test_cases = [
    # NameError - 编辑距离 1
    {
        'case_id': 'name_error_v1_01_edit_dist_1',
        'error_type': 'NameError',
        'description': '简单拼写错误：calculate_summ → calculate_sum (编辑距离 1)',
        'edit_distance': 1,
        'expected_similarity': 0.93,
        'error_message': "name 'calculate_summ' is not defined",
        'expected_fix': "Change 'calculate_summ' to 'calculate_sum'",
        'main_code': '''#!/usr/bin/env python3
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
'''
    },
    
    # NameError - 编辑距离 2
    {
        'case_id': 'name_error_v1_02_edit_dist_2',
        'error_type': 'NameError',
        'description': '拼写错误：proces_dat → process_data (编辑距离 2)',
        'edit_distance': 2,
        'expected_similarity': 0.85,
        'error_message': "name 'proces_dat' is not defined",
        'expected_fix': "Change 'proces_dat' to 'process_data'",
        'main_code': '''#!/usr/bin/env python3
def process_data(items):
    """处理数据"""
    return [x * 2 for x in items]

def main():
    values = [10, 20, 30]
    # 拼写错误：proces_dat (少了 s 和 a)
    result = proces_dat(values)
    print(f"Processed: {result}")

if __name__ == "__main__":
    main()
'''
    },
    
    # ImportError - 模块名拼写错误 (编辑距离 2)
    {
        'case_id': 'import_error_v1_01_module_typo',
        'error_type': 'ImportError',
        'description': '模块名拼写错误：authentification → authentication (编辑距离 2)',
        'edit_distance': 2,
        'expected_similarity': 0.87,
        'error_message': "No module named 'authentification'",
        'expected_fix': "Change import from 'authentification' to 'authentication'",
        'main_code': '''#!/usr/bin/env python3
# 拼写错误：authentification (多了 i，少了 c)
from authentification import verify_user

def main():
    user = "alice"
    if verify_user(user):
        print(f"Welcome {user}!")

if __name__ == "__main__":
    main()
''',
        'extra_files': {
            'authentication.py': '''#!/usr/bin/env python3
def verify_user(username):
    """验证用户"""
    return username in ["alice", "bob"]
'''
        }
    },
    
    # AttributeError - 方法名拼写错误 (编辑距离 1)
    {
        'case_id': 'attribute_error_v1_01_method_typo',
        'error_type': 'AttributeError',
        'description': '方法名拼写错误：get_confg → get_config (编辑距离 1)',
        'edit_distance': 1,
        'expected_similarity': 0.91,
        'error_message': "'Config' object has no attribute 'get_confg'",
        'expected_fix': "Change 'get_confg' to 'get_config'",
        'main_code': '''#!/usr/bin/env python3
class Config:
    def __init__(self):
        self.settings = {"debug": True, "port": 8000}
    
    def get_config(self, key):
        """获取配置"""
        return self.settings.get(key)

def main():
    config = Config()
    # 拼写错误：get_confg (少了 i)
    debug_mode = config.get_confg("debug")
    print(f"Debug: {debug_mode}")

if __name__ == "__main__":
    main()
'''
    },
    
    # TypeError - 函数名拼写错误 (编辑距离 1)
    {
        'case_id': 'type_error_v1_01_func_typo',
        'error_type': 'TypeError',
        'description': '函数名拼写错误：formaat_text → format_text (编辑距离 1)',
        'edit_distance': 1,
        'expected_similarity': 0.92,
        'error_message': "formaat_text() takes 1 positional argument but 2 were given",
        'expected_fix': "Change 'formaat_text' to 'format_text'",
        'main_code': '''#!/usr/bin/env python3
def format_text(text, width=80):
    """格式化文本"""
    return text.center(width)

def formaat_text(text):
    """错误的函数"""
    return text

def main():
    message = "Hello World"
    # 拼写错误：formaat_text (多了一个 a)
    result = formaat_text(message, 100)
    print(result)

if __name__ == "__main__":
    main()
'''
    },
    
    # NameError - 编辑距离 3 (边界情况)
    {
        'case_id': 'name_error_v1_03_edit_dist_3',
        'error_type': 'NameError',
        'description': '拼写错误：validat_inpt → validate_input (编辑距离 3)',
        'edit_distance': 3,
        'expected_similarity': 0.79,
        'error_message': "name 'validat_inpt' is not defined",
        'expected_fix': "Change 'validat_inpt' to 'validate_input'",
        'main_code': '''#!/usr/bin/env python3
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
'''
    }
]

# 创建测试用例
base_dir = Path(__file__).parent
for case in test_cases:
    create_test_case(base_dir, case)

print(f"\n✅ Created {len(test_cases)} V1 test cases")
