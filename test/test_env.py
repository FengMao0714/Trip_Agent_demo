"""测试环境变量加载脚本"""

import os
from dotenv import load_dotenv

# 1. 强制打印当前工作目录，看代码到底在哪里运行
print("Current Working Directory:", os.getcwd())

# 2. 检查 .env 文件在操作系统层面是否存在
env_path = os.path.join(os.getcwd(), '.env')
print(f"Is .env file exists on disk? {os.path.exists(env_path)}")

# 3. 尝试加载
load_dotenv()
print("LLM_API_KEY from env:", os.getenv('LLM_API_KEY'))