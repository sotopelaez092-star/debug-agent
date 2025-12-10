"""
测试ContextManager缓存功能
"""

import sys
import os
import time
import shutil
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.context_manager import ContextManager

def test_cache():
    """测试缓存加载性能"""
    
    # 创建临时测试项目
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = temp_dir
        
        # 创建一些测试文件
        os.makedirs(os.path.join(project_path, 'src'))
        
        # 创建10个Python文件模拟中型项目
        for i in range(10):
            with open(os.path.join(project_path, 'src', f'module_{i}.py'), 'w') as f:
                f.write(f"""
def function_{i}_a():
    pass

def function_{i}_b():
    pass

class Class_{i}:
    def method_a(self):
        pass
    
    def method_b(self):
        pass
""")
        
        # 创建主文件
        with open(os.path.join(project_path, 'main.py'), 'w') as f:
            f.write("from src.module_0 import function_0_a\nfunction_0_a()")
        
        print("=" * 60)
        print("测试ContextManager缓存功能")
        print("=" * 60)
        print(f"项目路径: {project_path}\n")
        
        # 第1次：无缓存，完整扫描
        print("🔍 第1次扫描（无缓存）...")
        start_time = time.time()
        cm1 = ContextManager(project_path, use_cache=True)
        duration1 = time.time() - start_time
        
        print(f"   耗时: {duration1:.3f}秒")
        print(f"   文件数: {len(cm1.file_contents)}")
        print(f"   符号数: {len(cm1.symbol_table)}\n")
        
        # 第2次：使用缓存
        print("🚀 第2次扫描（使用缓存）...")
        start_time = time.time()
        cm2 = ContextManager(project_path, use_cache=True)
        duration2 = time.time() - start_time
        
        print(f"   耗时: {duration2:.3f}秒")
        print(f"   文件数: {len(cm2.file_contents)}")
        print(f"   符号数: {len(cm2.symbol_table)}\n")
        
        # 计算提速
        if duration2 > 0:
            speedup = duration1 / duration2
            print("=" * 60)
            print(f"✅ 缓存提速: {speedup:.1f}x")
            print(f"   第1次: {duration1:.3f}秒")
            print(f"   第2次: {duration2:.3f}秒（节省 {duration1 - duration2:.3f}秒）")
            print("=" * 60)
        
        # 验证数据一致性
        assert len(cm1.file_contents) == len(cm2.file_contents), "文件数量不一致"
        assert len(cm1.symbol_table) == len(cm2.symbol_table), "符号表不一致"
        print("✅ 数据一致性检查通过\n")
        
        # 第3次：禁用缓存
        print("🔍 第3次扫描（禁用缓存）...")
        start_time = time.time()
        cm3 = ContextManager(project_path, use_cache=False)
        duration3 = time.time() - start_time
        print(f"   耗时: {duration3:.3f}秒\n")
        
        print("✅ 所有测试通过！")

if __name__ == "__main__":
    test_cache()
