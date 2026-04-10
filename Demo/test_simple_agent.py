from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, ToolRegistry
from hello_agents.tools import CalculatorTool
from my_simple_agent import MysimpleAgent

# 加载环境变量
load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM(provider="modelscope")

# 测试1：基础对话Agent(不使用工具)
print("\n=== 测试1：基础对话Agent(不使用工具) ===")
basic_agent = MysimpleAgent(
    name="基础助手",
    llm=llm,
    system_prompt="你是一个有用的智能助手,请用简洁明了的语言回答用户的问题。"
)

response1 = basic_agent.run("你好！请介绍一下你自己。")
print("基础助手的回答：", response1)
print()

# 测试2：启用工具调用的Agent
print("\n=== 测试2：启用工具调用的Agent ===")
tool_registry = ToolRegistry()
# 注册一个简单的计算工具
calculator = CalculatorTool()
tool_registry.register_tool(calculator)

enhanced_agent = MysimpleAgent(
    name="增强助手",
    llm=llm,
    system_prompt="你是一个有用的智能助手，能够使用工具来帮助用户解决问题。",
    tool_registry=tool_registry,
    enable_tool_calling=True
)

response2 = enhanced_agent.run("请帮我计算一下 111 * 8 + 112 的结果。")
print("增强助手的回答：", response2)
print()

# 测试3：流式响应
print("\n=== 测试3：流式响应 ===")
print("流式响应：", end=" ")
for chunk in basic_agent.stream_run("请解释什么是Harness engineering"):
    pass # 内容已经在stream_run方法中打印了

# 测试4：工具管理功能
print("\n=== 测试4：工具管理功能 ===")
print(f"添加工具前：{basic_agent.has_tools()}")
basic_agent.add_tool(calculator)
print(f"添加工具后：{basic_agent.has_tools()}")
print(f"可用工具列表：{basic_agent.list_tools()}")

# 查看对话历史
print("\n=== 对话历史 ===")
print(f"\n对话历史：{len(basic_agent.get_history())}条消息")