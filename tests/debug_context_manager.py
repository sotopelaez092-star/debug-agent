"""
调试ContextManager
"""
import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agent.context_manager import ContextManager


def main():
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"临时目录: {temp_dir}")
    
    # 创建测试文件
    utils_content = '''def calculate(a, b):
    """计算两个数的和"""
    return a + b
'''
    
    main_content = '''def test():
    result = calculate(10, 20)
    return result
'''
    
    # 写入文件
    with open(os.path.join(temp_dir, 'utils.py'), 'w') as f:
        f.write(utils_content)
    
    with open(os.path.join(temp_dir, 'main.py'), 'w') as f:
        f.write(main_content)
    
    print(f"创建的文件:")
    for file in os.listdir(temp_dir):
        print(f"  - {file}")
    
    # 初始化ContextManager
    print(f"\n初始化ContextManager...")
    cm = ContextManager(temp_dir)
    
    # 检查扫描结果
    print(f"\n扫描到的文件数量: {len(cm.file_contents)}")
    print("文件列表:")
    for file_path in cm.file_contents.keys():
        print(f"  - {file_path}")
    
    print(f"\n符号表: {cm.symbol_table}")
    
    # 测试get_context_for_error
    print(f"\n测试get_context_for_error...")
    try:
        context = cm.get_context_for_error(
            error_file="main.py",
            error_line=2,
            error_type="NameError",
            undefined_name="calculate"
        )
        print(f"✅ 成功!")
        print(f"找到的符号: {list(context['related_symbols'].keys())}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()