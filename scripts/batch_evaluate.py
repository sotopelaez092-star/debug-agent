"""批量评估30个测试案例"""
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()



sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.debug_agent import DebugAgent
import tempfile
import shutil


def setup_project_files(project_path, project_files):
    """设置项目文件"""
    os.makedirs(project_path, exist_ok=True)
    
    for file_path, content in project_files.items():
        full_path = os.path.join(project_path, file_path)
        
        # 创建子目录
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)


def evaluate_single_case(case, case_num, total):
    """评估单个测试案例"""
    
    print(f"\n{'='*60}")
    print(f"测试 {case_num}/{total}: {case['name']}")
    print(f"类别: {case['category']} | 错误: {case['error_type']} | 难度: {case['difficulty']}")
    print(f"{'='*60}")
    
    # 创建临时项目目录
    project_path = tempfile.mkdtemp(prefix=f"eval_case_{case['id']}_")
    
    try:
        # 设置项目文件
        setup_project_files(project_path, case['project_files'])
        
        # 准备buggy_code
        buggy_code = case['project_files'][case['error_file']]

        error_file = case['error_file']
        
        # 构造error_traceback
        error_traceback = f"""Traceback (most recent call last):
  File "{case['error_file']}", line 1, in <module>
{case['error_message']}
"""
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("请设置环境变量: export DEEPSEEK_API_KEY='your-key'")
        # 创建Agent
        agent = DebugAgent(project_path=project_path, api_key=api_key)
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行debug
        try:
            result = agent.debug(
                buggy_code=buggy_code,
                error_traceback=error_traceback,
                error_file=error_file,
                max_retries=2
            )
            elapsed_time = time.time() - start_time
            
            # 记录结果
            success = result.get('success', False)
            attempts = result.get('attempts', 0)
            
            print(f"✅ 成功: {success}")
            print(f"尝试次数: {attempts}")
            print(f"耗时: {elapsed_time:.2f}秒")
            
            if success:
                print(f"修复代码:\n{result['final_code'][:200]}...")
            else:
                print(f"失败原因: {result.get('error', 'Unknown')}")
            
            return {
                'case_id': case['id'],
                'case_name': case['name'],
                'category': case['category'],
                'error_type': case['error_type'],
                'difficulty': case['difficulty'],
                'success': success,
                'attempts': attempts,
                'elapsed_time': elapsed_time,
                'final_code': result.get('final_code', ''),
                'error': result.get('error', '') if not success else ''
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ 执行失败: {e}")
            
            return {
                'case_id': case['id'],
                'case_name': case['name'],
                'category': case['category'],
                'error_type': case['error_type'],
                'difficulty': case['difficulty'],
                'success': False,
                'attempts': 0,
                'elapsed_time': elapsed_time,
                'fixed_code': '',
                'error': str(e)
            }
    
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(project_path)
        except:
            pass


def main():
    """主函数"""
    
    print("="*60)
    print("批量评估开始")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. 读取测试集
    test_file = 'data/test_cases/week6_test_set.json'
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_cases = data['test_cases']
    total = len(test_cases)
    
    print(f"\n总计: {total}个测试案例")
    
    # 用户确认
    response = input("\n是否开始评估？(y/n): ")
    if response.lower() != 'y':
        print("取消评估")
        return
    
    # 2. 批量评估
    results = []
    
    for i, case in enumerate(test_cases, 1):
        result = evaluate_single_case(case, i, total)
        results.append(result)
        
        # 每5个案例显示进度
        if i % 5 == 0:
            success_count = sum(1 for r in results if r['success'])
            print(f"\n进度: {i}/{total} | 成功率: {success_count}/{i} ({success_count/i*100:.1f}%)")
    
    # 3. 保存结果
    output_file = 'data/evaluation/batch_results.json'
    os.makedirs('data/evaluation', exist_ok=True)
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_cases': total,
        'results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # 4. 统计分析
    print("\n" + "="*60)
    print("评估完成！")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_time = sum(r['elapsed_time'] for r in results)
    avg_time = total_time / total
    
    print(f"\n总体统计:")
    print(f"  总案例: {total}")
    print(f"  成功: {success_count}")
    print(f"  失败: {total - success_count}")
    print(f"  成功率: {success_count/total*100:.1f}%")
    print(f"  总耗时: {total_time:.1f}秒")
    print(f"  平均耗时: {avg_time:.1f}秒/案例")
    
    # 按类别统计
    print(f"\n按类别:")
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0}
        categories[cat]['total'] += 1
        if r['success']:
            categories[cat]['success'] += 1
    
    for cat, stats in categories.items():
        rate = stats['success'] / stats['total'] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    # 按错误类型统计
    print(f"\n按错误类型:")
    error_types = {}
    for r in results:
        err = r['error_type']
        if err not in error_types:
            error_types[err] = {'total': 0, 'success': 0}
        error_types[err]['total'] += 1
        if r['success']:
            error_types[err]['success'] += 1
    
    for err, stats in error_types.items():
        rate = stats['success'] / stats['total'] * 100
        print(f"  {err}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    # 失败案例
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n失败案例 ({len(failed)}个):")
        for r in failed[:10]:  # 只显示前10个
            print(f"  - 案例{r['case_id']}: {r['case_name']}")
            print(f"    错误: {r['error'][:100]}")
    
    print(f"\n✅ 结果已保存到: {output_file}")


if __name__ == '__main__':
    main()