import os
from typing import Optional, List, Dict, Any
from hello_agents import ToolRegistry
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

class MyAdvancedSearchTool:
    """
    自定义高级搜索工具类
    展示多源信息整合和智能选择的设计模式
    """

    def __init__(self):
        self.name = "my_advanced_search"
        self.description = "智能搜索工具，支持多个搜索源，自动选择最佳结果。"
        self.search_sources = []
        self._setup_search_sources()

    def _setup_search_sources(self):
        """设置可用的搜索源"""
        # 检查Tavily的可用性
        if os.getenv("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                self.search_sources.append("tavily")
                print("✅ Tavily搜索源已启用。")
            except ImportError:
                print("⚠️ Tavily库未安装，无法使用Tavily搜索源。")

        # 检查SerpAPI的可用性
        if os.getenv("SERPAPI_API_KEY"):
            try:
                import serpapi
                self.search_sources.append("serpapi")
                print("✅ SerpAPI搜索源已启用。")
            except ImportError:
                print("⚠️ SerpAPI库未安装，无法使用SerpAPI搜索源。")

        if self.search_sources:
            print(f"当前可用的搜索源：{', '.join(self.search_sources)}")
        else:
            print("⚠️ 没有可用的搜索源，请检查环境变量配置。")

    def search(self, query: str) -> str:
        """执行搜索，整合多个搜索源的结果"""
        if not query.strip():
            return "错误：搜索查询不能为空。"

        if not self.search_sources:
            return "错误：没有可用的搜索源。"
        
        print(f"开始智能搜索：{query}")

        # 尝试多个搜索源，返回最佳结果
        for source in self.search_sources:
            try:
                if source == "tavily":
                    result = self._search_with_tavily(query)
                    if result and "未找到" not in result:
                        return f"【Tavily搜索结果】\n\n{result}"
                elif source == "serpapi":
                    result = self._search_with_serpapi(query)
                    if result and "未找到" not in result:
                        return f"【SerpAPI搜索结果】\n\n{result}"
            except Exception as e:
                print(f"⚠️ 搜索源 '{source}' 出现错误: {str(e)}")
                continue
    
        return "所有搜索源都失败了，请检查网络连接和API配置。"
    
    def _search_with_tavily(self, query: str) -> str:
        """使用Tavily执行搜索"""
        response = self.tavily_client.search(query=query, max_results=3)

        if response.get("answer"):
            result = f"Ai直接答案：{response['answer']}\n\n"
        else:
            result = ""

        result += "相关结果：\n"
        for i, item in enumerate(response.get("results", [])[:3], 1):
            result += f"[{i}]{item.get('title', '')}\n"
            result += f"    {item.get('content', '')[:150]}...\n"
    
        return result

    def _search_with_serpapi(self, query: str) -> str:
        """使用SerpAPI执行搜索"""
        import serpapi

        search = serpapi.GoogleSearch({
            "q": query,
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "num": 3
        })
        results = search.get_dict()

        result = "Google搜索结果：\n"
        if "organic_result" in results:
            for i, res in enumerate(results["organic_results"][:3], 1):
                result += f"[{i}]{res.get('title', '')}\n"
                result += f"    {res.get('snippet', '')}\n"

        return result
    
def create_advanced_search_registry():
    """创建包含高级搜索工具的注册表"""
    registry = ToolRegistry()
    
    # 创建搜索工具实例
    search_tool = MyAdvancedSearchTool()

    # 注册搜索工具的方法作为函数

    registry.register_function(
        name="advanced_search",
        description="高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果。",
        func=search_tool.search
    )   
    return registry