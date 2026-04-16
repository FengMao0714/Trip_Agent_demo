# 配置好同级文件夹下.env中的大模型API, 可参考code文件夹配套的.env.example，也可以拿前几章的案例的.env文件复用。
# from hello_agents import SimpleAgent, HelloAgentsLLM
from dotenv import load_dotenv
from my_llm import MyLLM

# 加载环境变量
load_dotenv()

# 创建LLM实例 - 框架自动检测provider
# llm = HelloAgentsLLM()

# 或手动指定provider（可选）
llm = MyLLM(provider="modelscope")
message = [{"role": "user", "content": "请介绍一下自己。"}]
response = llm.think(message)

# # 创建SimpleAgent
# agent = SimpleAgent(
#     name="AI助手",
#     llm=llm,
#     system_prompt="你是一个有用的AI助手"
# )

# 基础对话
# response = agent.run("你好！请介绍一下自己")
print("LLM响应：")
for chunk in response:
    # 内部输出已在my_llm.py中处理，这里我们只需要获取最终结果即可
    pass

