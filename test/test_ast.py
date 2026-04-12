import ast

code = "x = 1 + 2"
# 把代码解析成一棵树
tree = ast.parse(code)

# 打印出这棵树的结构（Python 3.9+ 推荐用 dump）
print(ast.dump(tree, indent=4))