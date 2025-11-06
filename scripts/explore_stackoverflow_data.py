"""探索Stack Overflow数据"""
import pandas as pd

# 读取数据
print("📊 开始加载数据...")
df = pd.read_csv("data/raw/stackoverflow/QueryResults.csv")

# 基本信息
print(f"\n✅ 数据加载成功！")
print(f"📝 总行数: {len(df)}")
print(f"📝 列数: {len(df.columns)}")
print(f"\n📋 列名:\n{df.columns.tolist()}")

# 查看前几行
print(f"\n🔍 前5行数据:")
print(df.head())

# 数据类型
print(f"\n📊 数据类型:")
print(df.dtypes)

# 缺失值
print(f"\n❓ 缺失值统计:")
print(df.isnull().sum())