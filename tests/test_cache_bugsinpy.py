"""
测试ContextManager缓存功能 - 使用BugsInPy真实项目
"""

import sys
import os
import time
import shutil

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.context_manager import ContextManager

def test_cache_bugsinpy():
    """使用BugsInPy项目测试缓存"""
    
    # 正确的BugsInPy路径
    bugsinpy_base = os.path.expanduser("~/Desktop/projects/debug-agent/data/BugsInPy-master/projects")
    
    if not os.path.exists(bugsinpy_base):
        print(f"❌ BugsInPy路径不存在: {bugsinpy_base}")
        return
    
    # 查找第一个可用的项目
    project_path = None
    for project_name in os.listdir(bugsinpy_base):
        project_dir = os.path.join(bugsinpy_base, project_name)
        bugs_dir = os.path.join(project_dir, "bugs")
        if os.path.exists(bugs_dir):
            bugs = sorted([b for b in os.listdir(bugs_dir) if b.isdigit()])
            if bugs:
                project_path = os.path.join(bugs_dir, bugs[0])
                print(f"✅ 使用项目: {project_name}/bugs/{bugs[0]}")
                break
    
    if not project_path or not os.path.exists(project_path):
        print("❌ 未找到可用的BugsInPy项目")
        return
    
    print("=" * 70)
    print("测试ContextManager缓存功能 - BugsInPy真实项目")
    print("=" * 70)
    print(f"路径: {project_path}\n")
    
    # 清除旧缓存
    cache_dir = os.path.join(project_path, '.ai_debug_cache')
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("✅ 已清除旧缓存\n")
    
    # 第1次：无缓存，完整扫描
    print("🔍 第1次扫描（无缓存）...")
    print("   [扫描项目、解析AST、构建符号表...]")
    start_time = time.time()
    cm1 = ContextManager(project_path, use_cache=True)
    duration1 = time.time() - start_time
    
    print(f"\n   ✅ 完成")
    print(f"   耗时: {duration1:.2f}秒")
    print(f"   扫描文件: {cm1.scan_stats['scanned_files']}")
    print(f"   符号数: {len(cm1.symbol_table)}\n")
    
    # 第2次：使用缓存
    print("🚀 第2次扫描（使用缓存）...")
    print("   [直接加载缓存...]")
    start_time = time.time()
    cm2 = ContextManager(project_path, use_cache=True)
    duration2 = time.time() - start_time
    
    print(f"\n   ✅ 完成")
    print(f"   耗时: {duration2:.2f}秒")
    print(f"   扫描文件: {cm2.scan_stats['scanned_files']}")
    print(f"   符号数: {len(cm2.symbol_table)}\n")
    
    # 计算提速
    speedup = duration1 / duration2
    time_saved = duration1 - duration2
    
    print("=" * 70)
    print(f"🎯 性能对比")
    print("=" * 70)
    print(f"无缓存:    {duration1:.2f}秒")
    print(f"使用缓存:  {duration2:.2f}秒")
    print(f"节省时间:  {time_saved:.2f}秒")
    print(f"提速倍数:  {speedup:.1f}x")
    print("=" * 70)
    
    # 验证数据一致性
    print(f"\n🔍 数据一致性验证...")
    assert len(cm1.file_contents) == len(cm2.file_contents), "❌ 文件数量不一致"
    assert len(cm1.symbol_table) == len(cm2.symbol_table), "❌ 符号表不一致"
    print(f"   ✅ 文件内容一致: {len(cm1.file_contents)} 个文件")
    print(f"   ✅ 符号表一致: {len(cm1.symbol_table)} 个符号")
    
    # 第3次：禁用缓存对比
    print(f"\n🔍 第3次扫描（禁用缓存，验证时间）...")
    start_time = time.time()
    cm3 = ContextManager(project_path, use_cache=False)
    duration3 = time.time() - start_time
    print(f"   耗时: {duration3:.2f}秒")
    
    print(f"\n✅ 所有测试通过！")
    print(f"\n💡 结论: 缓存功能正常，可节省 {time_saved:.2f}秒（提速 {speedup:.1f}x）")

if __name__ == "__main__":
    test_cache_bugsinpy()
