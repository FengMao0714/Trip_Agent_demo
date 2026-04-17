import os
from dotenv import load_dotenv

# 必须是这一行！而且要放在所有 hello_agents 导入之前
load_dotenv()

os.environ["DASHSCOPE_API_KEY"] = "sk-2145b485510a4108bd13268e46ea9f54"
os.environ["EMBED_API_KEY"] = "sk-2145b485510a4108bd13268e46ea9f54"
os.environ["EMBED_MODEL_TYPE"] = "dashscope"
os.environ["EMBED_MODEL_NAME"] = "text-embedding-v3"
os.environ["MODELSCOPE_API_KEY"] = "sk-2145b485510a4108bd13268e46ea9f54"

# 检查一下（可选，用于调试）
print(f"DEBUG: 环境变量读取测试 -> {os.getenv('EMBED_API_KEY')[:5] if os.getenv('EMBED_API_KEY') else '未读到'}")
# 配置好同级文件夹下.env中的大模型API
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool


# 创建LLM实例
llm = HelloAgentsLLM(provider="modelscope")

# 创建Agent
agent = SimpleAgent(
    name="智能助手",
    llm=llm,
    system_prompt="你是一个有记忆和知识检索能力的AI助手"
)

# 创建工具注册表
tool_registry = ToolRegistry()

# 添加记忆工具
memory_tool = MemoryTool(user_id="user123")
tool_registry.register_tool(memory_tool)

# 添加RAG工具
rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
tool_registry.register_tool(rag_tool)

# 为Agent配置工具
agent.tool_registry = tool_registry

# 开始对话
response = agent.run("你好！请记住我叫张三，我是一名Python开发者")
print(response)
