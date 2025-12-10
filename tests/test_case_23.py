"""
单独测试 Case 23 - 多次运行验证稳定性
"""
import json
import sys
from pathlib import Path
import tempfile
import os

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

def main():
    # 1. 加载测试数据
    test_file = project_root / 'data/test_cases/week6_test_set.json'
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        test_cases = data['test_cases']
    
    # 2. 找到case 23
    case = None
    for tc in test_cases:
        if tc['id'] == 23:
            case = tc
            break
    
    if not case:
        print("❌ 找不到 case 23")
        return
    
    print("=" * 60)
    print(f"测试 Case {case['id']}: {case['name']}")
    print("=" * 60)
    print(f"类别: {case['category']}")
    print(f"错误类型: {case['error_type']}")
    print()
    
    # 3. 多次测试
    num_runs = 5
    results = []
    
    for i in range(num_runs):
        print(f"\n{'='*60}")
        print(f"第 {i+1}/{num_runs} 次运行")
        print('='*60)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入所有项目文件
            for filename, content in case['project_files'].items():
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
            
            # 调用ReActAgent
            agent = ReActAgent()
            result = agent.debug(
                buggy_code=case['project_files'][case['error_file']],
                error_traceback=f"Traceback:\n  File \"{case['error_file']}\"\n{case['error_message']}",
                project_path=tmpdir
            )
            
            results.append({
                'run': i + 1,
                'success': result['success'],
                'iterations': result['iterations']
            })
            
            print(f"✅ 成功: {result['success']}")
            print(f"🔄 迭代: {result['iterations']}")
    
    # 4. 统计
    print(f"\n{'='*60}")
    print("统计结果")
    print('='*60)
    success_count = sum(1 for r in results if r['success'])
    print(f"成功率: {success_count}/{num_runs} = {success_count/num_runs*100:.1f}%")
    
    if success_count > 0:
        avg_iterations = sum(r['iterations'] for r in results if r['success']) / success_count
        print(f"平均迭代次数（成功的）: {avg_iterations:.1f}")
    
    print("\n详细:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"  第{r['run']}次: {status} - {r['iterations']}次迭代")

if __name__ == '__main__':
    main()