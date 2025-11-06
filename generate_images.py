"""
为小红书生成中文配图
"""
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 设置输出目录
output_dir = Path('social_media/images')
output_dir.mkdir(parents=True, exist_ok=True)

# 配色方案（小红书风格）
COLORS = {
    'primary': '#FF2442',
    'secondary': '#FFB6C1',
    'success': '#52C41A',
    'text': '#333333',
    'bg': '#FFFFFF'
}


def generate_image1():
    """图1：错误类型分布饼图"""
    
    categories = {
        'TypeError': 5,
        'AttributeError': 4,
        'ValueError': 4,
        'IndexError': 3,
        'KeyError': 3,
        'NameError': 3,
        '其他类型': 18
    }
    
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    
    colors = ['#FF2442', '#FF6B6B', '#FFB6C1', '#FFA07A', 
              '#98D8C8', '#6BCB77', '#F7DC6F']
    
    wedges, texts, autotexts = ax.pie(
        categories.values(),
        labels=categories.keys(),
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 16, 'weight': 'bold'}
    )
    
    ax.set_title('Week1测试集-错误类型分布\n40个Python错误案例', 
                 fontsize=22, weight='bold', pad=20)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / '图1-错误类型分布.png', dpi=300, bbox_inches='tight')
    print("✅ 图1生成: 错误类型分布")
    plt.close()


def generate_image2():
    """图2：工具功能展示"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')
    
    # 左边：ErrorParser
    ax1.axis('off')
    ax1.text(0.5, 0.9, '错误解析器', ha='center', fontsize=24, weight='bold')
    ax1.text(0.5, 0.75, 'ErrorParser', ha='center', fontsize=18, 
             color=COLORS['primary'], weight='bold')
    
    features1 = [
        '· 提取错误类型',
        '· 识别对象类型',
        '· 定位属性名',
        '· 结构化输出'
    ]
    
    y_pos = 0.6
    for feature in features1:
        ax1.text(0.5, y_pos, feature, ha='center', fontsize=16)
        y_pos -= 0.12
    
    # 右边：CodeAnalyzer
    ax2.axis('off')
    ax2.text(0.5, 0.9, '代码分析器', ha='center', fontsize=24, weight='bold')
    ax2.text(0.5, 0.75, 'CodeAnalyzer', ha='center', fontsize=18,
             color=COLORS['primary'], weight='bold')
    
    features2 = [
        '· AST语法分析',
        '· 变量追踪',
        '· 函数识别',
        '· 问题检测'
    ]
    
    y_pos = 0.6
    for feature in features2:
        ax2.text(0.5, y_pos, feature, ha='center', fontsize=16)
        y_pos -= 0.12
    
    plt.suptitle('Week1核心工具', fontsize=26, weight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_dir / '图2-工具展示.png', dpi=300, bbox_inches='tight')
    print("✅ 图2生成: 工具展示")
    plt.close()


def generate_image3():
    """图3：时间规划对比"""
    
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
    
    tasks = ['数据准备', '测试集构建', '错误解析器', '代码分析器', '测试文档']
    planned = [1.5, 1.5, 2, 2, 1]
    actual = [0.5, 0.5, 1, 0.8, 0.2]
    
    x = range(len(tasks))
    width = 0.35
    
    bars1 = ax.barh([i - width/2 for i in x], planned, width, 
                     label='原计划', color='#FFB6C1', alpha=0.8)
    bars2 = ax.barh([i + width/2 for i in x], actual, width,
                     label='实际完成', color=COLORS['primary'], alpha=0.9)
    
    ax.set_yticks(x)
    ax.set_yticklabels(tasks, fontsize=14)
    ax.set_xlabel('天数', fontsize=16, weight='bold')
    ax.set_title('Week1时间规划对比\n原计划7天→实际2天完成！', 
                 fontsize=20, weight='bold', pad=20)
    
    ax.legend(fontsize=14, loc='lower right')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    for bars in [bars1, bars2]:
        for bar in bars:
            width_val = bar.get_width()
            ax.text(width_val, bar.get_y() + bar.get_height()/2, 
                   f'{width_val}天',
                   ha='left', va='center', fontsize=11, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / '图3-时间对比.png', dpi=300, bbox_inches='tight')
    print("✅ 图3生成: 时间对比")
    plt.close()


def generate_image4():
    """图4：项目统计卡片"""
    
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'Week1成果统计', 
            ha='center', fontsize=30, weight='bold')
    
    stats = [
        ('测试案例', '40', '个'),
        ('开发工具', '2', '个'),
        ('错误类型', '14', '种'),
        ('测试通过', '100', '%'),
        ('代码行数', '800+', '行'),
        ('完成时间', '2', '天')
    ]
    
    y_start = 0.8
    row_height = 0.13
    
    for i, (label, value, unit) in enumerate(stats):
        y = y_start - i * row_height
        
        if i % 2 == 0:
            rect = plt.Rectangle((0.1, y-0.05), 0.8, 0.1, 
                                facecolor='#FFF5F5', 
                                edgecolor=COLORS['primary'],
                                linewidth=2)
            ax.add_patch(rect)
        
        ax.text(0.15, y, label, fontsize=18, va='center')
        ax.text(0.75, y, f'{value}', 
               fontsize=26, weight='bold', 
               color=COLORS['primary'], 
               ha='right', va='center')
        ax.text(0.77, y, unit, fontsize=16, va='center')
    
    plt.tight_layout()
    plt.savefig(output_dir / '图4-项目统计.png', dpi=300, bbox_inches='tight')
    print("✅ 图4生成: 项目统计")
    plt.close()


if __name__ == '__main__':
    print("🎨 开始生成小红书配图（中文版）...\n")
    
    generate_image1()
    generate_image2()
    generate_image3()
    generate_image4()
    
    print(f"\n🎉 所有图片已生成！")
    print(f"📁 保存位置: {output_dir.absolute()}")
    print("\n生成的图片：")
    print("  1️⃣ 图1-错误类型分布.png")
    print("  2️⃣ 图2-工具展示.png")
    print("  3️⃣ 图3-时间对比.png")
    print("  4️⃣ 图4-项目统计.png")