"""
测试超级困难案例 - 多文件MVC架构
"""
import sys
from pathlib import Path
import tempfile
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

def main():
    # 案例数据
    case = {
        "id": 99,
        "name": "【极难】多文件循环依赖 + 初始化顺序问题",
        "category": "复杂",
        "error_type": "AttributeError",
        "project_files": {
            "main.py": """from models import User
from controllers import OrderController

def main():
    user = User("Tom")
    controller = OrderController(user)
    controller.create_order("Book", 29.99)
    controller.show_summary()

if __name__ == '__main__':
    main()
""",
            "models.py": """class User:
    def __init__(self, name):
        self.name = name
        self.orders = []
    
    def add_order(self, order):
        self.orders.append(order)
        
    def get_total_spent(self):
        return sum(order.price for order in self.orders)

class Order:
    def __init__(self, user, item, price):
        self.user = user
        self.item = item
        self.price = price
        user.add_order(self)
""",
            "controllers.py": """from models import Order
from views import OrderView

class OrderController:
    def __init__(self, user):
        self.user = user
        self.view = OrderView()
    
    def create_order(self, item, price):
        order = Order(self.user, item, price)
        self.view.display_order(order)
    
    def show_summary(self):
        self.view.display_summary(self.user)
""",
            "views.py": """class OrderView:
    def display_order(self, order):
        print(f"Created order: {order.item} - ${order.price}")
        print(f"Customer: {order.user.name}")
    
    def display_summary(self, user):
        print(f"\\nSummary for {user.name}:")
        print(f"Total orders: {len(user.orders)}")
        print(f"Total spent: ${user.total_spent}")
"""
        },
        "error_file": "views.py",
        "error_message": "AttributeError: 'User' object has no attribute 'total_spent'"
    }
    
    print("=" * 70)
    print(f"测试 Case {case['id']}: {case['name']}")
    print("=" * 70)
    print(f"错误类型: {case['error_type']}")
    print(f"涉及文件: {len(case['project_files'])} 个")
    print()
    
    # 创建临时项目
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入所有文件
        for filename, content in case['project_files'].items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
        
        print(f"项目路径: {tmpdir}")
        print()
        
        # 测试3次，看稳定性
        num_runs = 3
        results = []
        
        for i in range(num_runs):
            print(f"\n{'='*70}")
            print(f"第 {i+1}/{num_runs} 次运行")
            print('='*70)
            
            agent = ReActAgent()
            result = agent.debug(
                buggy_code=case['project_files'][case['error_file']],
                error_traceback=f"Traceback:\n  File \"{case['error_file']}\"\n{case['error_message']}",
                project_path=tmpdir
            )
            
            results.append({
                'run': i + 1,
                'success': result['success'],
                'iterations': result['iterations'],
                'fixed_code': result.get('fixed_code', '')
            })
            
            print(f"\n✅ 成功: {result['success']}")
            print(f"🔄 迭代: {result['iterations']}")
            
            if result['success']:
                print(f"\n修复后的代码:")
                print("-" * 60)
                print(result.get('fixed_code', ''))
        
        # 统计
        print(f"\n{'='*70}")
        print("统计结果")
        print('='*70)
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