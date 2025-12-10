#!/usr/bin/env python3
"""批量评估 30 个测试用例"""

import os, sys, time, subprocess, tempfile
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.agent.debug_agent import DebugAgent

# 30 个测试用例
TEST_CASES = [
    # NameError (10个)
    {"id": "NE01", "cat": "NameError", "code": "print(helllo)", "error": "NameError: name 'helllo' is not defined", "expect": None},
    {"id": "NE02", "cat": "NameError", "code": "def f(x):\n    return y\nprint(f(1))", "error": "NameError: name 'y' is not defined", "expect": None},
    {"id": "NE03", "cat": "NameError", "code": "total=0\nfor i in range(5):\n    totla+=i\nprint(total)", "error": "NameError: name 'totla' is not defined", "expect": "10"},
    {"id": "NE04", "cat": "NameError", "code": "name='Alice'\nprint(f'Hello {naem}')", "error": "NameError: name 'naem' is not defined", "expect": "Alice"},
    {"id": "NE05", "cat": "NameError", "code": "x=5\nprint(X)", "error": "NameError: name 'X' is not defined", "expect": "5"},
    {"id": "NE06", "cat": "NameError", "code": "result = vlaue * 2\nprint(result)", "error": "NameError: name 'vlaue' is not defined", "expect": None},
    {"id": "NE07", "cat": "NameError", "code": "nums=[1,2,3]\nfor n in nums:\n    smu+=n\nprint(sum)", "error": "NameError: name 'smu' is not defined", "expect": None},
    {"id": "NE08", "cat": "NameError", "code": "def greet():\n    print(mesage)\nmesage='Hi'\ngreet()", "error": "NameError: name 'mesage' is not defined", "expect": "Hi"},
    {"id": "NE09", "cat": "NameError", "code": "count=0\nconut+=1\nprint(count)", "error": "NameError: name 'conut' is not defined", "expect": "1"},
    {"id": "NE10", "cat": "NameError", "code": "data=[1,2,3]\nlenght=len(data)\nprint(lenght)", "error": "NameError: name 'lenght' is not defined", "expect": "3"},

    # TypeError (6个)
    {"id": "TE01", "cat": "TypeError", "code": "print('Price: $' + 100)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "100"},
    {"id": "TE02", "cat": "TypeError", "code": "print('Count: ' + 5)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "5"},
    {"id": "TE03", "cat": "TypeError", "code": "x='5'\nprint(x+3)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "8"},
    {"id": "TE04", "cat": "TypeError", "code": "def add(a,b):\n    return a+b\nprint(add([1,2],3))", "error": "TypeError: can only concatenate list (not \"int\") to list", "expect": None},
    {"id": "TE05", "cat": "TypeError", "code": "nums='123'\nprint(sum(nums))", "error": "TypeError: unsupported operand type(s) for +: 'int' and 'str'", "expect": "6"},
    {"id": "TE06", "cat": "TypeError", "code": "age=25\nprint('Age:'+age)", "error": "TypeError: can only concatenate str (not \"int\") to str", "expect": "25"},

    # AttributeError (5个)
    {"id": "AE01", "cat": "AttributeError", "code": "print('hello'.uper())", "error": "AttributeError: 'str' object has no attribute 'uper'", "expect": "HELLO"},
    {"id": "AE02", "cat": "AttributeError", "code": "nums=[3,1,2]\nnums.srot()\nprint(nums)", "error": "AttributeError: 'list' object has no attribute 'srot'", "expect": "[1, 2, 3]"},
    {"id": "AE03", "cat": "AttributeError", "code": "s='hello'\nprint(s.repalce('l','x'))", "error": "AttributeError: 'str' object has no attribute 'repalce'", "expect": "hexxo"},
    {"id": "AE04", "cat": "AttributeError", "code": "lst=[1,2,3]\nlst.apend(4)\nprint(lst)", "error": "AttributeError: 'list' object has no attribute 'apend'", "expect": "[1, 2, 3, 4]"},
    {"id": "AE05", "cat": "AttributeError", "code": "s='  hello  '\nprint(s.trimp())", "error": "AttributeError: 'str' object has no attribute 'trimp'", "expect": "hello"},

    # IndexError (3个)
    {"id": "IE01", "cat": "IndexError", "code": "print([1,2,3][3])", "error": "IndexError: list index out of range", "expect": "3"},
    {"id": "IE02", "cat": "IndexError", "code": "s='abc'\nprint(s[3])", "error": "IndexError: string index out of range", "expect": "c"},
    {"id": "IE03", "cat": "IndexError", "code": "def last(lst):\n    return lst[len(lst)]\nprint(last([1,2,3]))", "error": "IndexError: list index out of range", "expect": "3"},

    # KeyError (3个)
    {"id": "KE01", "cat": "KeyError", "code": "d={'a':1,'b':2}\nprint(d['c'])", "error": "KeyError: 'c'", "expect": None},
    {"id": "KE02", "cat": "KeyError", "code": "user={'name':'Tom','email':'t@t.com'}\nprint(user['emial'])", "error": "KeyError: 'emial'", "expect": "t@t.com"},
    {"id": "KE03", "cat": "KeyError", "code": "config={'host':'localhost'}\nprint(config['prot'])", "error": "KeyError: 'prot'", "expect": None},

    # ZeroDivisionError (2个)
    {"id": "ZE01", "cat": "ZeroDivisionError", "code": "print(10/0)", "error": "ZeroDivisionError: division by zero", "expect": None},
    {"id": "ZE02", "cat": "ZeroDivisionError", "code": "def avg(lst):\n    return sum(lst)/len(lst)\nprint(avg([]))", "error": "ZeroDivisionError: division by zero", "expect": None},

    # RecursionError (1个)
    {"id": "RE01", "cat": "RecursionError", "code": "def f(n):\n    return n*f(n-1)\nprint(f(5))", "error": "RecursionError: maximum recursion depth exceeded", "expect": "120"},
]

def run_code(code, timeout=5):
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

def main():
    print("\n" + "="*60)
    print("🧪 AI Debug Assistant 批量评估 (30个用例)")
    print("="*60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请配置 DEEPSEEK_API_KEY")
        return

    print(f"\n✅ API Key 已配置")
    print(f"📊 测试用例数: {len(TEST_CASES)}")

    agent = DebugAgent(api_key=api_key, project_path=".")

    results = []
    total_time = 0

    print("\n" + "-"*60)

    for i, tc in enumerate(TEST_CASES, 1):
        print(f"[{i:02d}/{len(TEST_CASES)}] {tc['id']}: {tc['cat']:<20}", end=" ", flush=True)

        start = time.time()
        try:
            res = agent.debug(
                buggy_code=tc['code'],
                error_traceback=f"Traceback (most recent call last):\n  File \"main.py\", line 1\n{tc['error']}",
                error_file="main.py",
                max_retries=1
            )
            elapsed = time.time() - start
            total_time += elapsed

            fixed = res.get('final_code', '')
            ai_ok = res.get('success', False)

            if ai_ok and fixed:
                run_res = run_code(fixed)
                runs = run_res['ok']
                output = run_res['out']
                if tc['expect'] is None:
                    correct = runs  # 只要能运行就算对
                else:
                    correct = tc['expect'] in output
            else:
                runs, correct, output = False, False, ""

            status = "✅" if correct else ("⚠️" if runs else "❌")
            print(f"{status} {elapsed:.1f}s | out: {output[:30] if output else 'N/A'}")

            results.append({
                'id': tc['id'],
                'cat': tc['cat'],
                'ai': ai_ok,
                'runs': runs,
                'correct': correct,
                'time': elapsed,
                'output': output
            })

        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ Error: {str(e)[:40]}")
            results.append({
                'id': tc['id'],
                'cat': tc['cat'],
                'ai': False,
                'runs': False,
                'correct': False,
                'time': elapsed,
                'error': str(e)
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
    print(f"   {'类别':<20} {'成功':<10} {'成功率':<10}")
    print(f"   {'-'*40}")

    for cat in ['NameError', 'TypeError', 'AttributeError', 'IndexError', 'KeyError', 'ZeroDivisionError', 'RecursionError']:
        cat_r = [r for r in results if r['cat'] == cat]
        if cat_r:
            ok = sum(1 for r in cat_r if r['correct'])
            print(f"   {cat:<20} {ok}/{len(cat_r):<8} {100*ok/len(cat_r):.0f}%")

    # 失败的用例
    failed = [r for r in results if not r['correct']]
    if failed:
        print(f"\n❌ 失败的用例 ({len(failed)}个):")
        for r in failed:
            print(f"   - {r['id']}: {r['cat']}")

    print("\n" + "="*60)
    print(f"🎯 最终成功率: {correct_ok}/{n} ({100*correct_ok/n:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    main()
