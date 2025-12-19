#!/usr/bin/env python3
def format_text(text, width=80):
    """格式化文本"""
    return text.center(width)

def formaat_text(text):
    """错误的函数"""
    return text

def main():
    message = "Hello World"
    # 拼写错误：formaat_text (多了一个 a)
    result = formaat_text(message, 100)
    print(result)

if __name__ == "__main__":
    main()
