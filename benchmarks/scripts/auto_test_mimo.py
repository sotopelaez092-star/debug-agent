#!/usr/bin/env python3
"""MiMo 自动化能力测试"""
import subprocess
import json
import time

tests = [
    {
        "name": "工具调用综合测试",
        "prompt": """请完成以下任务：
1. 运行 ls 命令
2. 创建文件 test.txt 内容为 "hello"
3. 读取 test.txt
4. 删除 test.txt

完成后说 "测试完成" """
    },
    {
        "name": "代码分析测试",
        "prompt": "分析 src/core/error_identifier.py 的主要功能（如果文件存在的话）"
    },
    {
        "name": "多轮对话测试",
        "prompt": "列出当前目录的 Python 文件"
    }
]

print("=" * 60)
print("MiMo 自动化测试")
print("=" * 60)

for i, test in enumerate(tests, 1):
    print(f"\n📝 测试 {i}: {test['name']}")
    print(f"Prompt: {test['prompt'][:50]}...")
    print("⏳ 请在 Claude Code 中运行此 prompt，观察结果")
    print(f"   完整 prompt:\n   {test['prompt']}")
    input("\n按回车继续下一个测试...")

print("\n✅ 所有测试 prompt 已展示")
print("请根据实际表现评估 MiMo 的能力")
