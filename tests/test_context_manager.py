# test_context_manager.py
"""
测试ContextManager扫描功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent.context_manager import ContextManager


def create_test_project():
    """创建一个测试项目结构"""
    # 创建临时目录
    test_dir = tempfile.mkdtemp(prefix="test_project_")
    
    # 创建项目结构
    structure = {
        "main.py": """import utils.calculator
from models.user import User

def main():
    result = utils.calculator.add(1, 2)
    user = User("test")
    print(result)
""",
        "utils/__init__.py": "",
        "utils/calculator.py": """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""",
        "models/__init__.py": "",
        "models/user.py": """class User:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
""",
        "tests/test_main.py": """import pytest
from main import main

def test_main():
    main()
""",
        # 应该被忽略的文件
        "venv/lib/python.py": "# 虚拟环境文件，应该被忽略",
        "__pycache__/main.cpython-39.pyc": "# 缓存文件，应该被忽略",
        ".git/config": "# Git配置，应该被忽略",
    }
    
    # 创建文件
    for file_path, content in structure.items():
        full_path = os.path.join(test_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        if file_path.endswith('.pyc'):
            # 二进制文件
            with open(full_path, 'wb') as f:
                f.write(b'binary content')
        else:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    return test_dir


def test_basic_scanning():
    """测试基本的扫描功能"""
    print("=" * 60)
    print("测试 ContextManager 扫描功能")
    print("=" * 60)
    
    # 创建测试项目
    test_dir = create_test_project()
    print(f"\n创建测试项目: {test_dir}")
    
    try:
        # 初始化ContextManager
        print("\n初始化 ContextManager...")
        cm = ContextManager(test_dir)
        
        # 获取扫描结果
        summary = cm.get_scan_summary()
        
        # 打印统计信息
        print("\n扫描统计:")
        print(f"  项目路径: {summary['project_path']}")
        print(f"  总文件数: {summary['stats']['total_files']}")
        print(f"  成功扫描: {summary['stats']['scanned_files']}")
        print(f"  跳过文件: {summary['stats']['skipped_files']}")
        print(f"  解析错误: {summary['stats']['parse_errors']}")
        
        # 打印扫描到的文件
        print(f"\n扫描到的Python文件 ({len(summary['files'])}个):")
        for file_path in sorted(summary['files']):
            print(f"  - {file_path}")
        
        # 验证结果
        print("\n验证结果:")
        expected_files = {
            "main.py",
            "utils/__init__.py", 
            "utils/calculator.py",
            "models/__init__.py",
            "models/user.py", 
            "tests/test_main.py"
        }
        
        # 转换路径格式（统一使用正斜杠）
        actual_files = {f.replace('\\', '/') for f in summary['files']}
        
        if actual_files == expected_files:
            print("✅ 扫描结果正确！所有Python文件都被找到")
        else:
            print("❌ 扫描结果不正确")
            print(f"   期望: {expected_files}")
            print(f"   实际: {actual_files}")
            print(f"   缺失: {expected_files - actual_files}")
            print(f"   多余: {actual_files - expected_files}")
        
        # 检查是否正确忽略了某些目录
        ignored_correctly = all(
            not any(f.startswith(ignored + '/') for f in summary['files'])
            for ignored in ['venv', '__pycache__', '.git']
        )
        
        if ignored_correctly:
            print("✅ 正确忽略了 venv/__pycache__/.git 目录")
        else:
            print("❌ 未正确忽略某些目录")
        
        # 查看某个文件的内容
        print("\n查看 main.py 的内容:")
        main_content = cm.file_contents.get("main.py", "未找到")
        print("-" * 40)
        print(main_content[:100] + "..." if len(main_content) > 100 else main_content)
        print("-" * 40)
        
        # 如果有错误，打印错误信息
        if summary['errors']:
            print("\n扫描过程中的错误:")
            for error in summary['errors']:
                print(f"  - {error['file']}: {error['error']} - {error['message']}")
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"\n清理测试目录: {test_dir}")
    
    print("\n测试完成！")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试错误处理")
    print("=" * 60)
    
    # 测试无效路径
    print("\n1. 测试无效路径:")
    try:
        cm = ContextManager("/path/that/does/not/exist")
    except FileNotFoundError as e:
        print(f"✅ 正确抛出异常: {e}")
    
    # 测试空路径
    print("\n2. 测试空路径:")
    try:
        cm = ContextManager("")
    except ValueError as e:
        print(f"✅ 正确抛出异常: {e}")
    
    # 测试文件而非目录
    print("\n3. 测试文件路径:")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        cm = ContextManager(tmp_path)
    except ValueError as e:
        print(f"✅ 正确抛出异常: {e}")
    finally:
        os.unlink(tmp_path)


def test_symbol_table():
    """测试符号表构建功能"""
    print("\n" + "=" * 60)
    print("测试符号表构建")
    print("=" * 60)
    
    # 创建测试项目
    test_dir = create_test_project()
    
    try:
        # 初始化ContextManager
        cm = ContextManager(test_dir)
        
        # 获取符号表摘要
        symbol_summary = cm.get_symbol_summary()
        
        print("\n符号表统计:")
        print(f"  总符号数: {symbol_summary['total_symbols']}")
        print(f"  函数数量: {symbol_summary['function_count']}")
        print(f"  类数量: {symbol_summary['class_count']}")
        print(f"  重名符号: {symbol_summary['duplicate_names']}")
        
        print(f"\n所有符号:")
        for symbol in sorted(symbol_summary['symbols']):
            info = cm.find_symbol(symbol)
            if isinstance(info, list):
                print(f"  - {symbol} (重名，{len(info)}个定义)")
                for i, def_info in enumerate(info):
                    print(f"    [{i+1}] {def_info['type']} in {def_info['file']}:{def_info['line']}")
            else:
                print(f"  - {symbol}: {info['type']} in {info['file']}:{info['line']}")
        
        # 测试查找具体符号
        print("\n测试查找符号:")
        
        # 查找 'add' 函数
        add_info = cm.find_symbol('add')
        if add_info:
            print(f"✅ 找到 'add' 函数:")
            print(f"   文件: {add_info['file']}")
            print(f"   行号: {add_info['line']}")
            print(f"   参数: {add_info['args']}")
        else:
            print("❌ 未找到 'add' 函数")
        
        # 查找 'User' 类
        user_info = cm.find_symbol('User')
        if user_info:
            print(f"✅ 找到 'User' 类:")
            print(f"   文件: {user_info['file']}")
            print(f"   行号: {user_info['line']}")
            print(f"   基类: {user_info['bases']}")
        else:
            print("❌ 未找到 'User' 类")
        
        # 查找不存在的符号
        fake_symbol = cm.find_symbol('non_existent_function')
        if fake_symbol is None:
            print("✅ 正确返回None对于不存在的符号")
        else:
            print("❌ 错误：不存在的符号应该返回None")
        
        # 验证预期结果
        expected_symbols = {
            'main': 'function',
            'add': 'function',
            'subtract': 'function',
            'User': 'class',
            'test_main': 'function'
        }
        
        print("\n验证结果:")
        all_correct = True
        for symbol, expected_type in expected_symbols.items():
            info = cm.find_symbol(symbol)
            if info and info['type'] == expected_type:
                print(f"  ✅ {symbol} ({expected_type})")
            else:
                print(f"  ❌ {symbol} - 期望: {expected_type}, 实际: {info['type'] if info else 'None'}")
                all_correct = False
        
        if all_correct:
            print("\n✅ 符号表测试全部通过！")
        else:
            print("\n❌ 部分测试失败")
            
    finally:
        # 清理
        shutil.rmtree(test_dir)
        print(f"\n清理测试目录: {test_dir}")


def test_duplicate_symbols():
    """测试重名符号处理"""
    print("\n" + "=" * 60)
    print("测试重名符号处理")
    print("=" * 60)
    
    # 创建有重名符号的测试项目
    test_dir = tempfile.mkdtemp(prefix="test_duplicate_")
    
    # 创建测试文件
    structure = {
        "module1.py": """def calculate(x, y):
    return x + y

class Helper:
    pass
""",
        "module2.py": """def calculate(a, b, c):
    return a * b + c

class Helper:
    def __init__(self):
        pass
""",
    }
    
    # 创建文件
    for file_path, content in structure.items():
        full_path = os.path.join(test_dir, file_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    try:
        # 初始化ContextManager
        cm = ContextManager(test_dir)
        
        # 查找重名符号
        calc_info = cm.find_symbol('calculate')
        helper_info = cm.find_symbol('Helper')
        
        print("\n重名符号 'calculate':")
        if isinstance(calc_info, list):
            print(f"✅ 正确处理为列表，共{len(calc_info)}个定义:")
            for i, info in enumerate(calc_info):
                print(f"  [{i+1}] 文件: {info['file']}, 参数: {info['args']}")
        else:
            print("❌ 应该返回列表")
        
        print("\n重名符号 'Helper':")
        if isinstance(helper_info, list):
            print(f"✅ 正确处理为列表，共{len(helper_info)}个定义:")
            for i, info in enumerate(helper_info):
                print(f"  [{i+1}] 文件: {info['file']}, 行号: {info['line']}")
        else:
            print("❌ 应该返回列表")
            
    finally:
        shutil.rmtree(test_dir)


def test_import_graph():
    """测试import依赖图构建"""
    print("\n" + "=" * 60)
    print("测试Import依赖图")
    print("=" * 60)
    
    # 创建测试项目
    test_dir = create_test_project()
    
    try:
        # 初始化ContextManager
        cm = ContextManager(test_dir)
        
        # 获取import摘要
        import_summary = cm.get_import_summary()
        
        print("\nImport统计:")
        print(f"  总文件数: {import_summary['total_files']}")
        print(f"  有import的文件: {import_summary['files_with_imports']}")
        print(f"  总import数: {import_summary['total_imports']}")
        
        print("\n各文件的import详情:")
        for file_path, details in import_summary['import_details'].items():
            print(f"\n文件: {file_path}")
            print(f"  Import数量: {details['import_count']}")
            print(f"  被Import次数: {details['imported_by_count']}")
            if details['imports']:
                print(f"  导入的模块: {details['imports']}")
            if details['imported_by']:
                print(f"  被这些文件导入: {details['imported_by']}")
        
        # 检查具体的import关系
        print("\n验证具体import关系:")
        
        # 检查main.py的imports
        main_imports = cm.import_graph.get("main.py", {}).get("imports", [])
        print(f"\nmain.py的imports ({len(main_imports)}个):")
        for imp in main_imports:
            if imp['type'] == 'import':
                print(f"  - import {imp['module']} (line {imp['line']})")
            else:
                names = [n['name'] for n in imp['names']]
                print(f"  - from {imp['module']} import {', '.join(names)} (line {imp['line']})")
        
        # 验证预期结果
        expected_imports = {
            'utils.calculator',  # import utils.calculator
            'models.user'        # from models.user import User
        }
        
        actual_modules = {imp['module'] for imp in main_imports}
        if actual_modules == expected_imports:
            print("\n✅ main.py的import识别正确")
        else:
            print(f"\n❌ main.py的import识别错误")
            print(f"   期望: {expected_imports}")
            print(f"   实际: {actual_modules}")
        
    finally:
        shutil.rmtree(test_dir)
        print(f"\n清理测试目录: {test_dir}")


def test_complex_imports():
    """测试复杂的import情况"""
    print("\n" + "=" * 60)
    print("测试复杂Import情况")
    print("=" * 60)
    
    # 创建包含各种import的测试项目
    test_dir = tempfile.mkdtemp(prefix="test_imports_")
    
    # 创建测试文件
    structure = {
        "app.py": """import os
import sys
from typing import List, Dict
import json as js
from collections import defaultdict
from .utils import helper  # 相对导入
from ..lib import core    # 多级相对导入
""",
        "utils.py": """import re
from datetime import datetime, timedelta
from math import *  # 导入所有
""",
        "models.py": """from __future__ import annotations  # 特殊import
import typing
from dataclasses import dataclass
""",
    }
    
    # 创建文件
    for file_path, content in structure.items():
        full_path = os.path.join(test_dir, file_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    try:
        # 初始化ContextManager
        cm = ContextManager(test_dir)
        
        # 分析app.py的imports
        app_imports = cm.import_graph.get("app.py", {}).get("imports", [])
        
        print("\napp.py的import分析:")
        print(f"总计: {len(app_imports)}个import语句")
        
        # 统计不同类型的import
        import_types = {'import': 0, 'from': 0}
        relative_imports = 0
        aliased_imports = 0
        
        for imp in app_imports:
            import_types[imp['type']] += 1
            if imp.get('level', 0) > 0:
                relative_imports += 1
            if imp.get('alias') or any(n.get('alias') for n in imp.get('names', [])):
                aliased_imports += 1
        
        print(f"  - 普通import: {import_types['import']}个")
        print(f"  - from import: {import_types['from']}个")
        print(f"  - 相对import: {relative_imports}个")
        print(f"  - 有别名的: {aliased_imports}个")
        
        # 检查特定的import
        print("\n特定import检查:")
        
        # 检查别名import
        json_import = next((imp for imp in app_imports if imp['module'] == 'json'), None)
        if json_import and json_import.get('alias') == 'js':
            print("✅ 正确识别别名: import json as js")
        else:
            print("❌ 未识别别名import")
        
        # 检查多个导入
        typing_import = next((imp for imp in app_imports if imp['module'] == 'typing'), None)
        if typing_import and len(typing_import.get('names', [])) == 2:
            print("✅ 正确识别多个导入: from typing import List, Dict")
        else:
            print("❌ 未识别多个导入")
        
        # 检查相对导入
        relative_count = sum(1 for imp in app_imports if imp.get('level', 0) > 0)
        if relative_count >= 1:
            print(f"✅ 识别了{relative_count}个相对导入")
        else:
            print("❌ 未识别相对导入")
        
    finally:
        shutil.rmtree(test_dir)
        print(f"\n清理测试目录: {test_dir}")


def test_import_resolution():
    """测试import解析为文件路径"""
    print("\n" + "=" * 60)
    print("测试Import路径解析")
    print("=" * 60)
    
    test_dir = create_test_project()
    
    try:
        cm = ContextManager(test_dir)
        
        # 测试解析模块到文件
        print("\n测试模块路径解析:")
        
        test_cases = [
            ("utils.calculator", "utils/calculator.py"),
            ("models.user", "models/user.py"),
            ("utils", "utils/__init__.py"),
            ("os", None),  # 外部模块
            ("json", None),  # 外部模块
        ]
        
        for module_name, expected_file in test_cases:
            import_info = {'module': module_name, 'type': 'import'}
            resolved = cm._resolve_import_to_file(import_info, "main.py")
            
            if resolved == expected_file:
                print(f"✅ {module_name} → {resolved or '外部模块'}")
            else:
                print(f"❌ {module_name} → 期望: {expected_file}, 实际: {resolved}")
        
        # 测试反向依赖
        print("\n测试反向依赖（谁导入了谁）:")
        
        # 检查utils/calculator.py被谁导入
        calc_file = "utils/calculator.py"
        if calc_file in cm.import_graph:
            imported_by = cm.import_graph[calc_file].get('imported_by', [])
            if 'main.py' in imported_by:
                print(f"✅ {calc_file} 被 main.py 导入")
            else:
                print(f"❌ {calc_file} 的反向依赖未正确记录")
        
    finally:
        shutil.rmtree(test_dir)


# 在main中添加新测试
if __name__ == "__main__":
    # 运行所有测试
    test_basic_scanning()
    test_error_handling()
    test_symbol_table()
    test_duplicate_symbols()
    test_import_graph()  # 新增
    test_complex_imports()  # 新增
    test_import_resolution()  # 新增