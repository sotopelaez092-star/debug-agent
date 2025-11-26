"""
测试后8个案例（案例23-30）- 简化版
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import json
import time
from src.agent.debug_agent import DebugAgent
from dotenv import load_dotenv
import os

load_dotenv()

def test_last_8_cases():
    """测试案例23-30"""
    
    test_cases_file = project_root / 'data/test_cases/week6_test_set.json'
    
    # 1. 加载测试案例
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. 判断数据结构
    if isinstance(data, list):
        all_cases = data
    elif isinstance(data, dict):
        # 可能有test_cases字段
        if 'test_cases' in data:
            all_cases = data['test_cases']
        elif 'cases' in data:
            all_cases = data['cases']
        else:
            # 尝试找第一个列表
            all_cases = next((v for v in data.values() if isinstance(v, list)), [])
    else:
        print("❌ 无法识别的数据格式")
        return
    
    print(f"✅ 加载了 {len(all_cases)} 个测试案例")
    
    # 3. 取案例23-30
    test_cases = []
    for case in all_cases:
        case_id = case.get('id') or case.get('case_id') or case.get('number')
        if case_id and 23 <= case_id <= 30:
            test_cases.append(case)
    
    if not test_cases:
        print("❌ 没找到案例23-30，显示前3个案例的结构：")
        for case in all_cases[:3]:
            print(json.dumps(case, indent=2, ensure_ascii=False)[:200])
        return
    
    print(f"📋 准备测试 {len(test_cases)} 个案例\n")
    
    # 4. 初始化Agent
    api_key = os.getenv("DEEPSEEK_API_KEY")
    project_path = project_root / 'data/test_projects/week6_test_project'
    
    agent = DebugAgent(
        api_key=api_key,
        project_path=str(project_path)
    )
    
    # 5. 逐个测试
    results = []
    
    for case in test_cases:
        case_id = case.get('id') or case.get('case_id')
        case_name = case.get('name') or case.get('description') or f"案例{case_id}"
        
        print(f"\n{'='*60}")
        print(f"🧪 案例 {case_id}: {case_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # 获取代码和错误
            buggy_code = case.get('code') or case.get('buggy_code')
            error_traceback = case.get('error') or case.get('traceback')
            error_file = case.get('error_file', 'main.py')
            
            result = agent.debug(
                buggy_code=buggy_code,
                error_traceback=error_traceback,
                error_file=error_file,
                max_retries=2
            )
            
            elapsed = time.time() - start_time
            
            if result['success']:
                print(f"✅ 成功！尝试 {result['total_attempts']} 次，耗时 {elapsed:.2f}秒")
            else:
                print(f"❌ 失败！尝试 {result['total_attempts']} 次，耗时 {elapsed:.2f}秒")
            
            results.append({
                'case_id': case_id,
                'case_name': case_name,
                'success': result['success'],
                'attempts': result['total_attempts'],
                'elapsed_time': elapsed
            })
            
        except Exception as e:
            print(f"❌ 出错: {e}")
            results.append({
                'case_id': case_id,
                'case_name': case_name,
                'success': False,
                'attempts': 0,
                'elapsed_time': 0,
                'error': str(e)
            })
    
    # 6. 汇总
    print(f"\n\n{'='*60}")
    print("📊 测试汇总")
    print(f"{'='*60}\n")
    
    success_count = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"成功: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print()
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} 案例{r['case_id']}: {r['case_name'][:40]:40s} | {r.get('attempts', 0)}次 | {r.get('elapsed_time', 0):.1f}s")

if __name__ == "__main__":
    test_last_8_cases()