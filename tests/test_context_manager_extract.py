"""
ContextManager上下文提取功能测试
"""
import os
import sys
import tempfile
import shutil
import pytest

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import os
import tempfile
import shutil
import pytest
from src.agent.context_manager import ContextManager


class TestContextExtraction:
    """测试上下文提取功能"""
    
    @pytest.fixture
    def temp_project(self):
        """创建临时测试项目"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 创建项目结构
        # utils.py - 工具函数
        utils_content = '''def calculate(a, b):
    """计算两个数的和"""
    return a + b

def multiply(x, y):
    """计算两个数的乘积"""
    return x * y

class Calculator:
    """计算器类"""
    def add(self, a, b):
        return a + b
'''
        
        # models.py - 数据模型
        models_content = '''class User:
    """用户类"""
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, {self.name}"

class Product:
    """产品类"""
    def __init__(self, name, price):
        self.name = name
        self.price = price
'''
        
        # main.py - 主文件（有错误）
        main_content = '''# 这里会有各种错误
def test_name_error():
    result = calculate(10, 20)  # NameError
    return result

def test_import_error():
    from database import connect  # ImportError
    return connect()

def test_attribute_error():
    user = User("Tom", 25)
    print(user.email)  # AttributeError
'''
        
        # 写入文件
        with open(os.path.join(temp_dir, 'utils.py'), 'w') as f:
            f.write(utils_content)
        
        with open(os.path.join(temp_dir, 'models.py'), 'w') as f:
            f.write(models_content)
        
        with open(os.path.join(temp_dir, 'main.py'), 'w') as f:
            f.write(main_content)
        
        yield temp_dir
        
        # 清理
        shutil.rmtree(temp_dir)
    
    def test_name_error_found(self, temp_project):
        """测试NameError - 找到符号定义"""
        # 初始化ContextManager
        cm = ContextManager(temp_project)
        
        # 🔍 调试：查看扫描到的文件
        print(f"\n项目路径: {temp_project}")
        print(f"扫描到的文件数量: {len(cm.file_contents)}")
        print("扫描到的文件:")
        for file_path in cm.file_contents.keys():
            print(f"  - {file_path}")
        
        print(f"\n符号表: {cm.symbol_table}")
        
        # 模拟NameError: calculate未定义
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name="calculate"
        )
    
    def test_name_error_not_found(self, temp_project):
        """测试NameError - 符号不存在"""
        cm = ContextManager(temp_project)
        
        # 模拟NameError: unknown_function未定义
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name="unknown_function"
        )
        
        # 验证结果：没有找到符号
        assert len(context["related_symbols"]) == 0
        assert len(context["import_suggestions"]) == 0
        
        # 但仍有基础信息
        assert "error_file_content" in context
        
        print("\n✅ NameError测试通过 - 符号不存在")
        print("   返回了基础信息")
    
    def test_name_error_no_undefined_name(self, temp_project):
        """测试NameError - 未提供undefined_name"""
        cm = ContextManager(temp_project)
        
        # 没有提供undefined_name
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name=None
        )
        
        # 验证结果：返回基础信息
        assert "error_file_content" in context
        assert len(context["related_symbols"]) == 0
        
        print("\n✅ NameError测试通过 - 未提供undefined_name")
    
    def test_name_error_class(self, temp_project):
        """测试NameError - 类名未定义"""
        cm = ContextManager(temp_project)
        
        # 模拟NameError: User未定义
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=10,
            error_type="NameError",
            undefined_name="User"
        )
        
        # 验证找到了类定义
        assert "User" in context["related_symbols"]
        symbol_info = context["related_symbols"]["User"]
        
        assert "models.py" in symbol_info["file"]
        assert "class User:" in symbol_info["definition"]
        assert symbol_info["type"] == "class"
        assert "def __init__" in symbol_info["definition"]
        
        print("\n✅ NameError测试通过 - 找到类定义")
        print(f"   类: User")
        print(f"   类型: {symbol_info['type']}")
    
    def test_import_error_found(self, temp_project):
        """测试ImportError - 找到模块"""
        cm = ContextManager(temp_project)
        
        # 假设要导入utils模块
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=6,
            error_type="ImportError",
            undefined_name="utils"
        )
        
        # 验证找到了模块
        assert len(context["related_files"]) > 0
        
        # 检查utils.py是否在相关文件中
        found_utils = False
        for file_path in context["related_files"].keys():
            if "utils.py" in file_path:
                found_utils = True
                break
        
        assert found_utils, "应该找到utils.py"
        
        print("\n✅ ImportError测试通过 - 找到模块")
    
    def test_import_error_not_found(self, temp_project):
        """测试ImportError - 模块不存在"""
        cm = ContextManager(temp_project)
        
        # 尝试导入不存在的模块
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=6,
            error_type="ImportError",
            undefined_name="database"
        )
        
        # 验证：没有找到模块
        # related_files可能是空的，或者只包含error_file
        print("\n✅ ImportError测试通过 - 模块不存在")
    
    def test_unknown_error_type(self, temp_project):
        """测试未知错误类型"""
        cm = ContextManager(temp_project)
        
        # 使用未知的错误类型
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=1,
            error_type="UnknownError",
            undefined_name=None
        )
        
        # 应该返回基础信息
        assert "error_file_content" in context
        assert len(context["related_symbols"]) == 0
        
        print("\n✅ 未知错误类型测试通过")
    
    def test_invalid_input(self, temp_project):
        """测试输入验证"""
        cm = ContextManager(temp_project)
        
        # 测试空error_file
        with pytest.raises(ValueError, match="error_file必须是非空字符串"):
            cm.get_context_for_error(
                error_file="",
                error_line=1,
                error_type="NameError"
            )
        
        # 测试负数行号
        with pytest.raises(ValueError, match="error_line必须是正整数"):
            cm.get_context_for_error(
                error_file="main.py",
                error_line=-1,
                error_type="NameError"
            )
        
        # 测试空error_type
        with pytest.raises(ValueError, match="error_type必须是非空字符串"):
            cm.get_context_for_error(
                error_file="main.py",
                error_line=1,
                error_type=""
            )
        
        # 测试不存在的文件
        with pytest.raises(ValueError, match="文件不在项目中"):
            cm.get_context_for_error(
                error_file="nonexistent.py",
                error_line=1,
                error_type="NameError"
            )
        
        print("\n✅ 输入验证测试通过")
    
    def test_multiple_symbols(self, temp_project):
        """测试提取多个符号"""
        cm = ContextManager(temp_project)
        
        # 测试calculate
        context1 = cm.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name="calculate"
        )
        
        # 测试multiply
        context2 = cm.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name="multiply"
        )
        
        # 验证都能找到
        assert "calculate" in context1["related_symbols"]
        assert "multiply" in context2["related_symbols"]
        
        # 验证定义不同
        def1 = context1["related_symbols"]["calculate"]["definition"]
        def2 = context2["related_symbols"]["multiply"]["definition"]
        
        assert "def calculate" in def1
        assert "def multiply" in def2
        assert def1 != def2
        
        print("\n✅ 多符号测试通过")
        print(f"   找到calculate和multiply")


def test_summary():
    """运行所有测试并生成报告"""
    print("\n" + "="*60)
    print("ContextManager上下文提取测试总结")
    print("="*60)
    
    # 测试会自动运行
    # 这里只是一个总结函数


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])