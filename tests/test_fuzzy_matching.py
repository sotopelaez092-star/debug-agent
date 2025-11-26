"""测试模糊匹配功能"""

import os
import sys
import tempfile
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.context_manager import ContextManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_import_error_fuzzy_matching():
    """测试ImportError的模糊匹配"""
    
    # 创建临时项目
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建utils.py
        utils_file = os.path.join(temp_dir, 'utils.py')
        with open(utils_file, 'w') as f:
            f.write("""
def calculate(a, b):
    return a + b

def process_data(data):
    return [x * 2 for x in data]
""")
        
        # 创建main.py（有错误的import）
        main_file = os.path.join(temp_dir, 'main.py')
        with open(main_file, 'w') as f:
            f.write("""
import utls  # 拼写错误！应该是utils

result = utls.calculate(1, 2)
print(result)
""")
        
        logger.info(f"临时项目: {temp_dir}")
        logger.info(f"文件: {os.listdir(temp_dir)}")
        
        # 初始化ContextManager
        cm = ContextManager(temp_dir)
        
        logger.info(f"file_contents: {list(cm.file_contents.keys())}")
        
        # 测试模糊匹配
        logger.info("\n" + "="*50)
        logger.info("🧪 测试模糊匹配: 'utls' → 'utils'")
        logger.info("="*50)
        
        context = cm.get_context_for_error(
            error_file='main.py',
            error_line=2,
            error_type='ModuleNotFoundError',
            undefined_name='utls'  # 拼写错误
        )
        
        # 检查结果
        logger.info("\n" + "="*50)
        logger.info("📊 测试结果")
        logger.info("="*50)
        
        logger.info(f"related_files: {list(context['related_files'].keys())}")
        logger.info(f"import_suggestions: {context['import_suggestions']}")
        
        # 验证
        if 'utils.py' in context['related_files']:
            logger.info("\n✅ 测试通过！模糊匹配成功")
            logger.info(f"找到了utils.py，内容长度: {len(context['related_files']['utils.py'])} 字符")
            return True
        else:
            logger.error("\n❌ 测试失败！没有找到utils.py")
            logger.error(f"related_files: {context['related_files']}")
            return False


    
def test_exact_matching():
    """测试精确匹配（不需要模糊匹配）"""
        
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建utils.py
        utils_file = os.path.join(temp_dir, 'utils.py')
        with open(utils_file, 'w') as f:
            f.write("def calculate(a, b): return a + b")
            
        # ========== 添加：创建main.py ==========
        main_file = os.path.join(temp_dir, 'main.py')
        with open(main_file, 'w') as f:
            f.write("""
import utils  # 正确的import

result = utils.calculate(1, 2)
print(result)
""")
        # ========================================
            
        # 初始化ContextManager
        cm = ContextManager(temp_dir)
        
        logger.info("\n" + "="*50)
        logger.info("🧪 测试精确匹配: 'utils' → 'utils'")
        logger.info("="*50)
        
        context = cm.get_context_for_error(
            error_file='main.py',
            error_line=2,
            error_type='ModuleNotFoundError',
            undefined_name='utils'  # 正确的名字
        )
        
        # 验证
        if 'utils.py' in context['related_files']:
            logger.info("✅ 精确匹配测试通过！")
            return True
        else:
            logger.error("❌ 精确匹配测试失败！")
            return False

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 开始测试模糊匹配功能")
    logger.info("="*60)
    
    # 测试1：模糊匹配
    result1 = test_import_error_fuzzy_matching()
    
    # 测试2：精确匹配
    result2 = test_exact_matching()
    
    # 总结
    logger.info("\n" + "="*60)
    logger.info("📊 测试总结")
    logger.info("="*60)
    logger.info(f"模糊匹配测试: {'✅ 通过' if result1 else '❌ 失败'}")
    logger.info(f"精确匹配测试: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        logger.info("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        logger.error("\n❌ 有测试失败！")
        sys.exit(1)