#!/usr/bin/env python3
"""
简化版批量测试 - 直接调用 LLM 修复，不依赖 RAG
"""

import os
import sys
import time
import subprocess
import tempfile
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 30 个测试用例
TEST_CASES = [
    # NameError (10个)
    {"id": "NE01", "cat": "NameError", "code": "print(helllo)", "error": "NameError: name 'helllo' is not defined", "expect": None},
    {"id": "NE02", "cat": "NameError", "code": "def f(x):\n    return y\nprint(f(1))", "error": "NameError: name 'y' is not defined", "expect": None},
    {"id": "NE03", "cat": "NameError", "code": "total=0\nfor i in range(5):\n    totla+=i\nprint(total)", "error": "NameError: name 'totla' is not defined", "expect": "10"},
    {"id": "NE04", "cat": "NameError", "code": "name='Alice'\nprint(f'Hello {naem}')", "error": "NameError: name 'naem' is not defined", "expect": "Alice"},
    {"id": "NE05", "cat": "NameError", "code": "x=5\nprint(X)", "error": "NameError: name 'X' is not defined", "expect": "5"},
    {"id": "NE06", "cat": "NameError", "code": "value=10\nresult = vlaue * 2\nprint(result)", "error": "NameError: name 'vlaue' is not defined", "expect": "20"},
    {"id": "NE07", "cat": "NameError", "code": "total=0\nnums=[1,2,3]\nfor n in nums:\n    toatl+=n\nprint(total)", "error": "NameError: name 'toatl' is not defined", "expect": "6"},
    {"id": "NE08", "cat": "NameError", "code": "message='Hi'\ndef greet():\n    print(mesage)\ngreet()", "error": "NameError: name 'mesage' is not defined", "expect": "Hi"},
    {"id": "NE09", "cat": "NameError", "code": "count=0\ncount+=1\nprint(coutn)", "error": "NameError: name 'coutn' is not defined", "expect": "1"},
    {"id": "NE10", "cat": "NameError", "code": "data=[1,2,3]\nlength=len(data)\nprint(lenght)", "error": "NameError: name 'lenght' is not defined", "expect": "3"},

    # TypeError (6个)
    {"id": "TE01", "cat": "TypeError", "code": "print('Price: $' + 100)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "100"},
    {"id": "TE02", "cat": "TypeError", "code": "print('Count: ' + 5)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "5"},
    {"id": "TE03", "cat": "TypeError", "code": "x='5'\ny=3\nprint(x+y)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "8"},
    {"id": "TE04", "cat": "TypeError", "code": "def add(a,b):\n    return a+b\nprint(add([1,2],3))", "error": "TypeError: can only concatenate list (not \"int\") to list", "expect": None},
    {"id": "TE05", "cat": "TypeError", "code": "nums=[1,2,3]\nprint(sum(nums)/len)", "error": "TypeError: unsupported operand type(s) for /: 'int' and 'builtin_function_or_method'", "expect": "2"},
    {"id": "TE06", "cat": "TypeError", "code": "age=25\nprint('Age: '+age)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "25"},

    # AttributeError (5个)
    {"id": "AE01", "cat": "AttributeError", "code": "print('hello'.uper())", "error": "AttributeError: 'str' object has no attribute 'uper'", "expect": "HELLO"},
    {"id": "AE02", "cat": "AttributeError", "code": "nums=[3,1,2]\nnums.srot()\nprint(nums)", "error": "AttributeError: 'list' object has no attribute 'srot'", "expect": "[1, 2, 3]"},
    {"id": "AE03", "cat": "AttributeError", "code": "s='hello'\nprint(s.repalce('l','x'))", "error": "AttributeError: 'str' object has no attribute 'repalce'", "expect": "hexxo"},
    {"id": "AE04", "cat": "AttributeError", "code": "lst=[1,2,3]\nlst.apend(4)\nprint(lst)", "error": "AttributeError: 'list' object has no attribute 'apend'", "expect": "[1, 2, 3, 4]"},
    {"id": "AE05", "cat": "AttributeError", "code": "s='  hello  '\nprint(s.stip())", "error": "AttributeError: 'str' object has no attribute 'stip'", "expect": "hello"},

    # IndexError (3个)
    {"id": "IE01", "cat": "IndexError", "code": "print([1,2,3][3])", "error": "IndexError: list index out of range", "expect": "3"},
    {"id": "IE02", "cat": "IndexError", "code": "s='abc'\nprint(s[3])", "error": "IndexError: string index out of range", "expect": "c"},
    {"id": "IE03", "cat": "IndexError", "code": "def last(lst):\n    return lst[len(lst)]\nprint(last([1,2,3]))", "error": "IndexError: list index out of range", "expect": "3"},

    # KeyError (3个)
    {"id": "KE01", "cat": "KeyError", "code": "d={'a':1,'b':2}\nprint(d['c'])", "error": "KeyError: 'c'", "expect": None},
    {"id": "KE02", "cat": "KeyError", "code": "user={'name':'Tom','email':'t@t.com'}\nprint(user['emial'])", "error": "KeyError: 'emial'", "expect": "t@t.com"},
    {"id": "KE03", "cat": "KeyError", "code": "config={'host':'localhost','port':8080}\nprint(config['prot'])", "error": "KeyError: 'prot'", "expect": "8080"},

    # ZeroDivisionError (2个)
    {"id": "ZE01", "cat": "ZeroDivisionError", "code": "print(10/0)", "error": "ZeroDivisionError: division by zero", "expect": None},
    {"id": "ZE02", "cat": "ZeroDivisionError", "code": "def avg(lst):\n    return sum(lst)/len(lst)\nprint(avg([]))", "error": "ZeroDivisionError: division by zero", "expect": None},

    # RecursionError (1个)
    {"id": "RE01", "cat": "RecursionError", "code": "def factorial(n):\n    return n*factorial(n-1)\nprint(factorial(5))", "error": "RecursionError: maximum recursion depth exceeded", "expect": "120"},
]


def run_code(code: str, timeout: int = 5) -> dict:
    """执行代码并返回结果"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        r = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=timeout)
        return {'ok': r.returncode == 0, 'out': r.stdout.strip(), 'err': r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'out': '', 'err': 'Timeout'}
    except Exception as e:
        return {'ok': False, 'out': '', 'err': str(e)}
    finally:
        os.unlink(tmp)


def fix_code_with_llm(client: OpenAI, buggy_code: str, error: str) -> dict:
    """直接调用 LLM 修复代码"""
    prompt = f"""修复以下 Python 代码中的错误。

错误代码:
```python
{buggy_code}
```

错误信息: {error}

请只返回修复后的完整代码，不要任何解释。代码用 ```python 和 ``` 包裹。
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        # 提取代码
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()

        return {'success': True, 'fixed_code': code}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    print("\n" + "="*60)
    print("🧪 AI Debug Assistant 批量评估 (30个用例)")
    print("   直接调用 DeepSeek API 测试")
    print("="*60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请配置 DEEPSEEK_API_KEY")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )

    print(f"\n✅ API 已连接")
    print(f"📊 测试用例数: {len(TEST_CASES)}")

    results = []
    total_time = 0

    print("\n" + "-"*60)

    for i, tc in enumerate(TEST_CASES, 1):
        print(f"[{i:02d}/{len(TEST_CASES)}] {tc['id']}: {tc['cat']:<20}", end=" ", flush=True)

        start = time.time()

        # Step 1: LLM 修复
        fix_result = fix_code_with_llm(client, tc['code'], tc['error'])

        elapsed = time.time() - start
        total_time += elapsed

        ai_ok = fix_result.get('success', False)
        fixed_code = fix_result.get('fixed_code', '')

        # Step 2: 执行验证
        if ai_ok and fixed_code:
            run_result = run_code(fixed_code)
            runs = run_result['ok']
            output = run_result['out']

            # Step 3: 检查输出
            if tc['expect'] is None:
                correct = runs
            else:
                correct = tc['expect'] in output
        else:
            runs, correct, output = False, False, ""

        status = "✅" if correct else ("⚠️" if runs else "❌")
        out_preview = output[:25] + "..." if len(output) > 25 else output
        print(f"{status} {elapsed:.1f}s | {out_preview if output else 'N/A'}")

        results.append({
            'id': tc['id'],
            'cat': tc['cat'],
            'ai': ai_ok,
            'runs': runs,
            'correct': correct,
            'time': elapsed,
            'output': output,
            'fixed_code': fixed_code
        })

    # ============ 统计结果 ============
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    n = len(results)
    ai_ok = sum(1 for r in results if r['ai'])
    runs_ok = sum(1 for r in results if r['runs'])
    correct_ok = sum(1 for r in results if r['correct'])

    print(f"\n📈 总体指标:")
    print(f"   AI修复成功: {ai_ok}/{n} ({100*ai_ok/n:.1f}%)")
    print(f"   代码能运行: {runs_ok}/{n} ({100*runs_ok/n:.1f}%)")
    print(f"   输出正确:   {correct_ok}/{n} ({100*correct_ok/n:.1f}%)")
    print(f"   总耗时:     {total_time:.1f}s")
    print(f"   平均耗时:   {total_time/n:.2f}s")

    print(f"\n📊 按错误类别统计:")
    print(f"   {'类别':<20} {'成功/总数':<12} {'成功率':<10}")
    print(f"   {'-'*45}")

    categories = ['NameError', 'TypeError', 'AttributeError', 'IndexError', 'KeyError', 'ZeroDivisionError', 'RecursionError']
    for cat in categories:
        cat_r = [r for r in results if r['cat'] == cat]
        if cat_r:
            ok = sum(1 for r in cat_r if r['correct'])
            print(f"   {cat:<20} {ok}/{len(cat_r):<10} {100*ok/len(cat_r):.0f}%")

    # 失败的用例
    failed = [r for r in results if not r['correct']]
    if failed:
        print(f"\n❌ 失败的用例 ({len(failed)}个):")
        for r in failed:
            reason = "AI修复失败" if not r['ai'] else ("代码无法运行" if not r['runs'] else "输出不符预期")
            print(f"   - {r['id']}: {r['cat']} ({reason})")

    print("\n" + "="*60)
    print(f"🎯 最终成功率: {correct_ok}/{n} ({100*correct_ok/n:.1f}%)")
    print("="*60)

    # 保存详细结果
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': n,
                'ai_fix_rate': ai_ok/n,
                'run_rate': runs_ok/n,
                'correct_rate': correct_ok/n,
                'avg_time': total_time/n
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 详细结果已保存到: test_results.json")


if __name__ == "__main__":
    main()
