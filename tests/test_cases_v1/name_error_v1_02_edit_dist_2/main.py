#!/usr/bin/env python3
def process_data(items):
    """处理数据"""
    return [x * 2 for x in items]

def main():
    values = [10, 20, 30]
    # 拼写错误：proces_dat (少了 s 和 a)
    result = proces_dat(values)
    print(f"Processed: {result}")

if __name__ == "__main__":
    main()
