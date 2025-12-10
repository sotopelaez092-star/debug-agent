#!/usr/bin/env python3
"""
测试 BugsInPy FastAPI Bug 7
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/FiaShi/Desktop/projects/debug-agent')

from src.agent.debug_agent import DebugAgent

# 从环境变量获取API key
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not set")
    print("Run: export DEEPSEEK_API_KEY='your-key'")
    sys.exit(1)

# 错误代码（从exception_handlers.py读取）
with open('mock_fastapi_project/fastapi/exception_handlers.py', 'r') as f:
    buggy_code = f.read()

# 模拟的错误traceback
error_traceback = """Traceback (most recent call last):
  File "fastapi/exception_handlers.py", line 22, in request_validation_exception_handler
    content={"detail": jsonable_encoder(exc.errors())},
NameError: name 'jsonable_encoder' is not defined
"""

# 创建Agent
print("🚀 Creating DebugAgent...")
agent = DebugAgent(
    project_path="./mock_fastapi_project",
    api_key=api_key
)

# 运行测试
print("\n" + "="*60)
print("🧪 Testing BugsInPy FastAPI Bug 7")
print("="*60)

result = agent.debug(
    buggy_code=buggy_code,
    error_traceback=error_traceback,
    max_retries=2
)

# 输出结果
print("\n" + "="*60)
print("📊 Test Result")
print("="*60)
print(f"✅ Success: {result['success']}")
print(f"🔄 Attempts: {result['attempts']}")

if result['success']:
    print(f"\n📝 Explanation:\n{result['explanation']}")
    print(f"\n💾 Fixed Code:\n{result['fixed_code'][:200]}...")
else:
    print(f"\n❌ Failed after {result['attempts']} attempts")
    if 'error' in result:
        print(f"Error: {result['error']}")

print("\n" + "="*60)
