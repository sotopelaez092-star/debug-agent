# src/utils/test_llm.py
"""
测试LLM连接
验证DeepSeek API是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.llm_factory import get_llm
from src.utils.config import get_settings


def test_llm_basic():
    """测试基础LLM调用"""
    print("=" * 50)
    print("测试1: 基础LLM调用")
    print("=" * 50)
    
    try:
        # 获取LLM
        llm = get_llm()
        
        # 简单测试
        response = llm.invoke("Say 'Hello from DeepSeek!' in one sentence")
        
        print(f"✅ 响应: {response.content}")
        print(f"✅ Token使用: {response.response_metadata}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_llm_chinese():
    """测试中文支持"""
    print("\n" + "=" * 50)
    print("测试2: 中文理解")
    print("=" * 50)
    
    try:
        llm = get_llm(temperature=0.3)
        
        response = llm.invoke("用一句话解释什么是RAG（检索增强生成）")
        
        print(f"✅ 响应: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_llm_code():
    """测试代码生成"""
    print("\n" + "=" * 50)
    print("测试3: 代码生成")
    print("=" * 50)
    
    try:
        llm = get_llm(temperature=0.1)
        
        prompt = """Write a Python function to calculate factorial. 
Only return the code, no explanation."""
        
        response = llm.invoke(prompt)
        
        print(f"✅ 响应:\n{response.content}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_config():
    """测试配置加载"""
    print("\n" + "=" * 50)
    print("测试4: 配置加载")
    print("=" * 50)
    
    try:
        settings = get_settings()
        
        print(f"LLM Provider: {settings.llm_provider}")
        print(f"LLM Model: {settings.llm_model}")
        print(f"Temperature: {settings.llm_temperature}")
        print(f"Chunk Size: {settings.chunk_size}")
        
        # 检查API Key是否配置
        if settings.deepseek_api_key:
            masked_key = settings.deepseek_api_key[:8] + "..." + settings.deepseek_api_key[-4:]
            print(f"✅ DeepSeek API Key: {masked_key}")
        else:
            print("❌ DeepSeek API Key未配置！")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 开始测试LLM连接...\n")
    
    results = {
        "配置加载": test_config(),
        "基础调用": test_llm_basic(),
        "中文支持": test_llm_chinese(),
        "代码生成": test_llm_code(),
    }
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！DeepSeek API配置正确。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
    
    sys.exit(0 if all_passed else 1)