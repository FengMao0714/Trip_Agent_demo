import ast
import operator
import math
from hello_agents import ToolRegistry

def my_calculator(expression: str) -> str:
    """
    一个简单的计算器工具函数，支持基本的算术运算和一些数学函数
    """
    if not expression.strip():
        return "错误：表达式不能为空。"
    
    # 支持的基本运算
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg
    }

    # 支持的基本函数
    functions = {
        'sqrt': math.sqrt,
        'log': math.log,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan
    }

    try:
        node = ast.parse(expression, mode='eval')
        result = _eval_node(node.body, operators, functions)
        return str(result)
    except:
        return "错误：无效的表达式语法。"
    
def _eval_node(node, operators, functions):
    """简化的表达式求值"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, operators, functions)
        right = _eval_node(node.right, operators, functions)
        op = operators.get(type(node.op))
        return op(left, right)
    elif isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg, operators, functions) for arg in node.args]
            return functions[func_name](*args)
    elif isinstance(node, ast.Name):
        if node.id in functions:
            return functions[node.id]
        
def create_calculator_registry():
    """创建一个包含计算器工具的工具注册表"""
    registry = ToolRegistry()

    # 注册计算器工具，直接传入表达式字符串
    registry.register_function(
        name="my_calculator",
        description="简单的数学计算工具，支持基本的算术运算和一些数学函数。输入表达式字符串，例如 '2 + 3 * 4' 或 'sqrt(16)'。",
        func=my_calculator
    )
    return registry