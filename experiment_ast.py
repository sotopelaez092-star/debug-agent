import ast

# 示例代码
code = """
x = None
print(x.name)
"""

# 解析为AST
tree = ast.parse(code)

# 打印AST结构
print(ast.dump(tree, indent=2))