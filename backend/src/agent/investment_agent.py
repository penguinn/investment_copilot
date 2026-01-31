"""
投资建议 Agent - 基于 ReAct 架构
"""

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from src.agent.memory import ConversationMemory, LongTermMemory
from src.agent.tools import NewsTool, SearchTool
from src.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL_AGENT

logger = logging.getLogger(__name__)

# 百炼平台 OpenAI 兼容接口
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# ReAct 系统提示词
SYSTEM_PROMPT = """你是一位专业的投资顾问 AI 助手。你需要根据用户的问题，使用可用的工具获取信息，然后给出专业的投资建议。

## 工作流程（ReAct 模式）
1. **Thought（思考）**: 分析用户问题，确定需要哪些信息
2. **Action（行动）**: 调用工具获取所需信息
3. **Observation（观察）**: 分析工具返回的结果
4. 重复上述步骤直到获得足够信息
5. **Answer（回答）**: 综合所有信息，给出投资建议

## 可用工具
1. **get_news**: 从数据库获取财经新闻（政策、市场快讯等）
2. **web_search**: 搜索互联网获取最新信息

## 建议原则
1. 分析当前市场环境和主要风险
2. 识别潜在的投资机会
3. 推荐具体的投资方向（板块、行业）
4. 建议客观专业，同时提示风险
5. **不推荐具体的股票代码**

## 回答格式
请用以下格式回答用户：

### 市场分析
（基于获取的新闻和搜索结果，分析当前市场环境）

### 投资机会
（识别到的投资机会和利好板块）

### 推荐方向
- 板块/行业1: 原因
- 板块/行业2: 原因

### 风险提示
（需要关注的风险因素）

{user_context}
"""


class InvestmentAgent:
    """投资建议 Agent"""

    def __init__(
        self,
        user_id: str = "default",
        session_id: str = None,
    ):
        """
        初始化 Agent
        :param user_id: 用户ID（用于长期记忆）
        :param session_id: 会话ID（用于短期记忆）
        """
        self.user_id = user_id
        self.session_id = session_id or f"{user_id}_{id(self)}"

        # 初始化 LLM 客户端
        if DASHSCOPE_API_KEY:
            self.client = OpenAI(
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
            )
        else:
            self.client = None
            logger.warning("DASHSCOPE_API_KEY not configured")

        # 初始化工具
        self.tools = {
            "get_news": NewsTool(),
            "web_search": SearchTool(),
        }

        # 初始化记忆
        self.short_memory = ConversationMemory(self.session_id)
        self.long_memory = LongTermMemory(self.user_id)

        # 最大迭代次数（防止无限循环）
        self.max_iterations = 5

    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取工具的 schema"""
        return [tool.to_schema() for tool in self.tools.values()]

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """执行工具"""
        if tool_name not in self.tools:
            return f"未知工具: {tool_name}"

        tool = self.tools[tool_name]
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            result = tool.run(**arguments)
            logger.debug(f"Tool result: {result[:200]}...")
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"工具执行失败: {str(e)}"

    def _build_system_prompt(self) -> str:
        """构建系统提示词（包含用户上下文）"""
        user_context = self.long_memory.get_context_for_agent()
        if user_context:
            user_context = f"\n## 用户上下文\n{user_context}"
        return SYSTEM_PROMPT.format(user_context=user_context)

    def chat(self, user_message: str) -> str:
        """
        与 Agent 对话
        :param user_message: 用户消息
        :return: Agent 回复
        """
        if not self.client:
            return "Agent 未配置，请设置 DASHSCOPE_API_KEY 环境变量。"

        # 添加用户消息到短期记忆
        self.short_memory.add_message("user", user_message)

        # 构建消息列表
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self.short_memory.get_messages_for_llm(),
        ]

        iteration = 0
        final_response = ""

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}")

            try:
                # 调用 LLM
                response = self.client.chat.completions.create(
                    model=DASHSCOPE_MODEL_AGENT,
                    messages=messages,
                    tools=self._get_tools_schema(),
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=4000,
                )

                assistant_message = response.choices[0].message

                # 检查是否需要调用工具
                if assistant_message.tool_calls:
                    # 添加 assistant 消息
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in assistant_message.tool_calls
                        ],
                    })

                    # 执行每个工具调用
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            arguments = {}

                        # 执行工具
                        tool_result = self._execute_tool(tool_name, arguments)

                        # 添加工具结果
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        })

                    # 继续下一轮迭代
                    continue

                else:
                    # 没有工具调用，返回最终回复
                    final_response = assistant_message.content or "抱歉，我无法生成回复。"
                    break

            except Exception as e:
                logger.error(f"Agent error: {e}")
                final_response = f"处理请求时发生错误: {str(e)}"
                break

        # 添加回复到短期记忆
        self.short_memory.add_message("assistant", final_response)

        # 保存到长期记忆（如果是投资建议）
        if "推荐方向" in final_response or "投资" in final_response:
            self.long_memory.save_recommendation(
                final_response[:500],  # 只保存前500字
                metadata={"query": user_message},
            )

        return final_response

    def get_investment_advice(self, topic: str = None) -> str:
        """
        获取投资建议（便捷方法）
        :param topic: 特定主题（如"新能源"、"军工"等）
        """
        if topic:
            query = f"请分析{topic}板块的投资机会，给出投资建议。"
        else:
            query = "请根据最新的财经新闻，分析当前市场环境，给出投资建议。"

        return self.chat(query)

    def clear_session(self):
        """清除当前会话"""
        self.short_memory.clear()

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.client is not None
