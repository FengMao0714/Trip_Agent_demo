import os
from typing import Optional
from openai import OpenAI
from hello_agents import HelloAgentsLLM

class MyLLM(HelloAgentsLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = "auto",
        **kwargs
    ):
        # 检查provider是否为我们象处理的 'modelscope'
        if provider == "modelscope":
            print("使用ModelScope作为LLM提供者")
            self.provider = "modelscope"

            # 从环境变量获取ModelScope的API密钥和基础URL
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

            # 检查API密钥是否存在
            if not self.api_key:
                raise ValueError("请提供ModelScope的API密钥，或在环境变量中设置MODELSCOPE_API_KEY")
            
            # 设置默认模型和其他参数
            self.model = model or os.getenv("MODELSCOPE_MODEL_ID") or "tongyi-xiaomi-analysis-pro"
            self.temperature = kwargs.get("temperature", 0.7)
            self.max_tokens = kwargs.get("max_tokens",512)
            self.timeout = kwargs.get("timeout", 60)

            # 使用获取到的参数创建OpenAI客户端实例
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        else:
            # 如果provider不是'modelscope'，则调用父类的初始化方法
            super().__init__(model=model, api_key=api_key, base_url=base_url, provider=provider, **kwargs)