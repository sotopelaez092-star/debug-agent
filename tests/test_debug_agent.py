import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.debug_agent import DebugAgent

def test_debug_agent_very_hard():
    """测试非常难的bug - 多个连锁错误"""
    
    buggy_code = """
import json

def load_user_data(user_id):
    filename = f"user_{user_id}.jsn"
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def calculate_discount(user_id):
    user = load_user_data(user_id)
    age = user['age']
    if age > 60:
        return 0.2
    elif age > 18:
        return 0.1
    else:
        return 0

# 测试
discount = calculate_discount(123)
print(f"折扣: {discount}")
"""
    
    error_traceback = """
Traceback (most recent call last):
  File "test.py", line 19, in <module>
    discount = calculate_discount(123)
  File "test.py", line 10, in calculate_discount
    user = load_user_data(user_id)
  File "test.py", line 5, in load_user_data
    with open(filename, 'r') as f:
FileNotFoundError: [Errno 2] No such file or directory: 'user_123.jsn'
"""

    print("\n" + "="*60)
    print("🧪 测试案例：多个连锁错误（文件+JSON+类型）")
    print("="*60)
    print("\n💡 预期修复路径：")
    print("  第1次：修复文件扩展名 .jsn → .json")
    print("         但会遇到新错误：文件还是不存在")
    print("  第2次：添加文件不存在处理")
    print("         但可能遇到：KeyError (age不存在)")
    print("  第3次：完整处理所有异常")
    print()
    
    agent = DebugAgent()
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback,
        max_retries=2
    )
    
    # 打印详细结果
    print("\n" + "="*60)
    print("🎯 Debug结果")
    print("="*60)
    print(f"{'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"总尝试次数: {result['total_attempts']}")
    
    # 打印每次尝试的详细信息
    print(f"\n🔄 详细尝试记录:")
    print("="*60)
    for i, attempt in enumerate(result['attempts']):
        print(f"\n【第 {attempt['attempt_number']} 次尝试】")
        print(f"状态: {'✅ 成功' if attempt['verification']['success'] else '❌ 失败'}")
        
        print(f"\n📝 修复思路:")
        explanation = attempt['explanation']
        # 分段打印，更易读
        for line in explanation.split('\n')[:5]:  # 只打印前5行
            print(f"  {line}")
        if len(explanation.split('\n')) > 5:
            print("  ...")
        
        if attempt['changes']:
            print(f"\n🔧 修改内容:")
            for change in attempt['changes'][:3]:  # 只打印前3个改动
                print(f"  • {change}")
        
        if not attempt['verification']['success']:
            print(f"\n❌ 失败原因:")
            stderr = attempt['verification'].get('stderr', '')
            # 提取关键错误行
            error_lines = [line for line in stderr.split('\n') if line.strip()]
            for line in error_lines[-3:]:  # 只打印最后3行
                print(f"  {line}")
        else:
            print(f"\n✅ 验证通过:")
            stdout = attempt['verification'].get('stdout', '')
            if stdout:
                print(f"  输出: {stdout[:100]}")
        
        print("-" * 60)
    
    # 打印最终代码
    print(f"\n📝 最终代码:")
    print("="*60)
    print(result['final_code'])
    print("="*60)
    
    # 总结
    if result['success']:
        print(f"\n🎉 成功！经过 {result['total_attempts']} 次尝试完成修复")
    else:
        print(f"\n😞 失败！经过 {result['total_attempts']} 次尝试仍未成功")


if __name__ == "__main__":
    test_debug_agent_very_hard()