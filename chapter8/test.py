import os
from dotenv import load_dotenv

# 1. 强行雷达搜索并加载 .env
load_dotenv()

# 2. X光检测一：看看 Python 到底读到 Key 没有？
api_key = os.getenv("EMBED_API_KEY")
if api_key:
    print(f"【X光测试 1】成功读到 Key: {api_key[:5]}...{api_key[-4:]}") # 截取头尾，防止泄露
else:
    print("【X光测试 1】失败！读到的 Key 是 None，说明 .env 没加载上！")

# 3. X光检测二：看看 dashscope 库到底装了没有？
try:
    import dashscope
    print(f"【X光测试 2】dashscope 库正常，版本: {dashscope.__version__}")
except ImportError:
    print("【X光测试 2】失败！当前虚拟环境没装 dashscope，请执行 pip install dashscope")

print("-" * 40) # 分割线

# ... 下面保留你原本的 main.py 代码（比如 from hello_agents... 等）