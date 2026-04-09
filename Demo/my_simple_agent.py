from typing import Optional, Iterator
from hello_agents import SimpleAgent, HelloAgentsLLM, Config, Message, ToolRegistry
import re

class MysimpleAgent(SimpleAgent):
    """
    重写的简单对话Agent
    展示了如何基于框架基类构建自定义Agent
    """
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        print(f"{name}初始化完成，工具调用 {'启用' if self.enable_tool_calling else '禁用'}。")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        重写的运行方法-实现简单的对话逻辑，展示如何调用工具
        """
        print(f"{self.name}正在处理：{input_text}")

        #构建详细列表
        messages = []

        #添加系统消息（可能包含工具信息）
        enhanced_system_prompt  =self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})

        #添加历史消息
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        #添加当前用户消息
        messages.append({"role": "user", "content": input_text})

        #如果没有启用工具调用，直接调用LLM生成响应
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            print(f"{self.name}生成响应完成")
            return response
        
        #启用工具调用的逻辑，支持多轮工具调用
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)

    def _get_enhanced_system_prompt(self) -> str:
        """构建包含工具信息的系统提示词"""
        base_prompt = self.system_prompt or "你是一个有用的智能助手。"

        if not self.enable_tool_calling and not self.tool_registry:
            return base_prompt
        
        #获取工具描述
        tools_description = self.tool_registry.get_tools_description() 
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt
        
        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题:\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## 工具调用格式\n"
        tools_section += "当你需要使用工具时，请按照以下格式输出：\n"
        tools_section += "`[TOOL_CALL:search:Python编程]`或`[TOOL_CALL:memory:recall=用户信息]`\n\n"
        tools_section += "工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"

        return base_prompt + tools_section

    def _run_with_tools(self, messages: list, input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """支持工具调用的运行逻辑，允许多轮工具调用"""
        current_iteration = 0
        final_response = ""
        
        while current_iteration < max_tool_iterations:
            #调用LLM生成响应
            response = self.llm.invoke(messages, **kwargs)

            #检查响应中是否包含工具调用指令
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                print(f"检测到{len(tool_calls)}个工具调用指令，正在处理...")
                #处理每个工具调用指令,并收集结果
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # 从响应中移除工具调用指令，替换为工具结果
                    clean_response = clean_response.replace(call['original'], "")

                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})

                # 添加工具结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "assistant", "content": f"工具调用结果:\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"})

                current_iteration += 1
                continue  # 继续下一轮迭代，允许多轮工具调用
            
            #如果没有工具调用指令，说明生成完成
            final_response = response
            break
        
        # 如果超过最大工具调用次数，仍未生成最终响应，选择最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)
            print(f"⚠️ 已达到最大工具调用次数，返回最后一次生成的响应。")

        # 更新历史消息
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        print(f"{self.name}生成响应完成")

        return final_response
    
    def _parse_tool_calls(self, text: str) -> list:
        """解析文本中的工具调用"""
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        matches = re.findall(pattern, text)

        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append({
                "tool_name": tool_name.strip(), 
                "parameters": parameters.strip(),
                "original": f"[TOOL_CALL:{tool_name}:{parameters}]"
            })
        return tool_calls
    
    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """执行工具调用"""
        if not self.tool_registry:
            return f"错误：未配置工具注册表，无法执行工具调用。"
        
        try:
            # 智能参数解析
            if tool_name == "calculator":
                # 计算机工具直接传入表达式
                return self.tool_registry.execute_tool(tool_name, parameters)
            else:
                # 其他工具可以传入原始参数使用智能参数解析
                param_dict = self._parse_tool_parameters(tool_name, parameters)
                tool = self.tool_register.get_tool(tool_name)
                if not tool:
                    return f"错误：未找到名为 '{tool_name}' 的工具。"
                result = tool.run(param_dict)

            return f"工具 '{tool_name}' 执行结果: {result}"
        except Exception as e:
            return f"错误：执行工具 '{tool_name}' 时发生异常: {str(e)}"
        
    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """智能解析工具参数，支持多种格式"""
        param_dict = {}

        # 尝试解析为键值对格式：key=value,key2=value2
        if "=" in parameters:
            if ',' in parameters:
                # 多个参数：action=search,query=Python编程,limit=5
                pairs = parameters.split(",")
                for pair in pairs:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        param_dict[key.strip()] = value.strip()
            else:
                # 单个参数：query=Python编程
                key, value = parameters.split("=", 1)
                param_dict[key.strip()] = value.strip()
        else:
            # 其他格式直接传入原始字符串,根据工具类型智能推断
            if tool_name == "search":
                param_dict = {'query': parameters}
            elif tool_name == "memory":
                param_dict = {'action': 'search', 'query': parameters}
            else:
                param_dict = {'input': parameters}

        return param_dict
    
    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """
        自定义的流式运行方法，展示如何在流式生成中处理工具调用
        """
        print(f"{self.name}正在流式处理：{input_text}")

        # 构建初始消息列表
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": input_text})
        
        # 流式调用LLM生成响应
        full_response = ""
        print(f"{self.name}正在流式生成响应...", end="")
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            print(chunk, end="", flush=True)
            yield chunk
        
        print() # 换行

        # 更新历史消息
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
        print(f"{self.name}流式生成响应完成")

    def add_tool(self, tool) -> None:
        """添加工具到Agent(便利方法)"""
        if not self.tool_registry:
            from hello_agents import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        self.tool_registry.register_tool(tool)
        print(f"工具 '{tool.name}' 已添加到Agent '{self.name}'。")

    def has_tools(self) -> bool:
        """检查Agent是否配置了工具"""
        return self.enable_tool_calling and self.tool_registry is not None
    
    def remove_tool(self, tool_name: str) -> None:
        """从Agent中移除工具"""
        if self.tool_registry:
            self.tool_registry.unregister(tool_name)
            return True
        return False
    
    def list_tools(self) -> list:
        """列出Agent当前配置的工具"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []