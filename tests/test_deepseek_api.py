# tests/test_deepseek_api.py
"""
测试 Deepseek API 接口
"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

from openai import OpenAI

# 获取API配置
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")

# 验证配置
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY 未配置")

print(f"✅API Key: {api_key[:10]}")
print(f"✅Base URL: {base_url}")

def test_deepseek():
    """测试DeepSeek API 接口"""
    print("\n🧪 开始测试DeepSeek API...")

    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 调用API
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的测试助手"},
                {"role": "user", "content": "你好"}
            ],
            max_tokens=50
        )

        # 提取回复
        reply = response.choices[0].message.content
        print(f"✅ API调用成功！")
        print(f"📝 回复：{reply}")
        return True

    except Exception as e:
        print(f"❌ API调用失败：{str(e)}")
        return False


if __name__ == "__main__":
    test_deepseek()