# V2 Benchmark 测试使用指南

## 📋 文件说明

已创建以下文件：

1. **test_v2_benchmark.py** - 核心测试脚本
2. **compare_models.sh** - 自动对比测试脚本
3. **V2_BENCHMARK_TEST_GUIDE.md** - 本使用指南

## 🚀 使用方法

### 方法 1: 只测试 MiMo (推荐先用这个)

```bash
# 1. 配置 MiMo
export ANTHROPIC_BASE_URL="https://your-mimo-api.com"
export ANTHROPIC_AUTH_TOKEN="your-mimo-key"

# 2. 快速测试（6个用例，约5分钟）
python3 test_v2_benchmark.py --quick

# 或完整测试（30个用例，约20分钟）
python3 test_v2_benchmark.py
```

### 方法 2: MiMo vs Claude 自动对比

```bash
# 1. 先配置 MiMo
export ANTHROPIC_BASE_URL="https://your-mimo-api.com"
export ANTHROPIC_AUTH_TOKEN="your-mimo-key"

# 2. 运行对比测试（自动测试两个模型）
chmod +x compare_models.sh

# 快速对比（6个用例）
./compare_models.sh --quick

# 完整对比（30个用例）
./compare_models.sh
```

### 方法 3: 分步测试

```bash
# Step 1: 测试 MiMo
export ANTHROPIC_BASE_URL="https://your-mimo-api.com"
export ANTHROPIC_AUTH_TOKEN="your-mimo-key"
python3 test_v2_benchmark.py --quick

# Step 2: 测试 Claude
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
python3 test_v2_benchmark.py --quick

# Step 3: 手动对比结果文件
ls -t v2_test_*.json | head -2
```

## 📊 测试结果

测试完成后会生成：

### 结果文件

- `v2_test_mimo_20251219_xxxxxx.json` - MiMo 测试结果
- `v2_test_claude_20251219_xxxxxx.json` - Claude 测试结果

### 结果内容

```json
{
  "timestamp": "20251219_153045",
  "model": "mimo",
  "total": 6,
  "success_count": 5,
  "success_rate": 83.3,
  "avg_duration": 12.5,
  "avg_confidence": 0.856,
  "by_type": {
    "NameError": {
      "total": 1,
      "success": 1,
      "durations": [10.2],
      "confidences": [0.92]
    }
  },
  "results": [...]
}
```

## 📈 关键指标

### 1. 成功率
- **优秀**: > 80%
- **良好**: 60-80%
- **一般**: < 60%

### 2. 平均耗时
- **快速**: < 15秒
- **正常**: 15-30秒
- **较慢**: > 30秒

### 3. 平均置信度
- **高**: > 0.85
- **中**: 0.70-0.85
- **低**: < 0.70

## 🎯 快速开始（3步）

### Step 1: 配置 MiMo
```bash
export ANTHROPIC_BASE_URL="https://your-mimo-api.com"
export ANTHROPIC_AUTH_TOKEN="your-mimo-key"
```

### Step 2: 运行快速测试
```bash
chmod +x compare_models.sh
./compare_models.sh --quick
```

### Step 3: 查看结果
测试完成后会自动显示对比报告，例如：
```
======================================================================
对比报告
======================================================================

指标                  MiMo                 Claude               差异
----------------------------------------------------------------------
成功率                  83.3%                85.6%              -2.3%
平均耗时                12.5s                14.2s              -1.7s
平均置信度              0.856                0.892              -0.036

💡 评价:
   ✅ 两者成功率接近 (差异 -2.3%)
   ⚡ MiMo 速度更快 (-1.7s)
```

## 🔧 高级用法

### 限制测试数量
```bash
# 只测试前 10 个用例
python3 test_v2_benchmark.py --limit 10
```

### 只测试某个模型
```bash
# 只测试 MiMo
./compare_models.sh --mimo-only

# 只测试 Claude
./compare_models.sh --claude-only
```

### 查看帮助
```bash
./compare_models.sh --help
python3 test_v2_benchmark.py --help
```

## ⚠️ 注意事项

1. **首次运行会较慢** - ContextTools 需要建立索引
2. **确保测试用例存在** - 需要 `tests/test_cases_v2/` 目录
3. **API 配置正确** - MiMo 必须支持 Anthropic API 格式
4. **网络稳定** - 测试过程需要多次 API 调用

## 🐛 常见问题

### Q1: 提示找不到模块
```bash
# 确保在项目根目录运行
cd /Users/FiaShi/Desktop/debug-agent
python3 test_v2_benchmark.py --quick
```

### Q2: MiMo API 连接失败
```bash
# 检查配置
echo $ANTHROPIC_BASE_URL
echo ${ANTHROPIC_AUTH_TOKEN:0:10}...

# 测试连接
curl $ANTHROPIC_BASE_URL/v1/messages \
  -H "x-api-key: $ANTHROPIC_AUTH_TOKEN" \
  -H "content-type: application/json" \
  -d '{"model":"test","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

### Q3: 所有测试都失败
```bash
# 检查测试用例是否存在
ls tests/test_cases_v2/*/case_*/main.py

# 手动运行一个用例
cd tests/test_cases_v2/name_error/case_01_refactored_function
python3 main.py
```

## 📞 获取帮助

如果遇到问题：
1. 查看错误信息
2. 检查配置是否正确
3. 确认测试用例文件完整
4. 查看结果文件中的详细错误

---

**快速开始命令（复制粘贴）**:

```bash
cd /Users/FiaShi/Desktop/debug-agent
export ANTHROPIC_BASE_URL="https://your-mimo-api.com"
export ANTHROPIC_AUTH_TOKEN="your-key"
chmod +x compare_models.sh
./compare_models.sh --quick
```
