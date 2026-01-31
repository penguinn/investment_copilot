"""
阿里百炼平台 Qwen 模型客户端（使用 OpenAI 兼容模式）
"""

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from src.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL, DASHSCOPE_MODEL_SUMMARY

logger = logging.getLogger(__name__)

# 百炼平台 OpenAI 兼容接口地址
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class QwenClient:
    """Qwen大模型客户端（OpenAI兼容模式）"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        初始化Qwen客户端
        :param api_key: 百炼平台API Key，默认从环境变量读取
        :param model: 模型名称，默认qwen-turbo
        """
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model or DASHSCOPE_MODEL

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=DASHSCOPE_BASE_URL,
            )
        else:
            self.client = None
            logger.warning("DASHSCOPE_API_KEY not configured")

    def _call(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.8,
        model: str = None,
    ) -> Optional[str]:
        """
        调用Qwen模型
        :param messages: 消息列表 [{"role": "user", "content": "..."}]
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :param top_p: 核采样参数
        :param model: 指定模型，默认使用初始化时的模型
        :return: 模型返回的文本
        """
        if not self.client:
            logger.error("DASHSCOPE_API_KEY not configured, cannot call LLM")
            return None

        try:
            completion = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            return completion.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to call Qwen model: {e}")
            return None

    def chat(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """
        简单对话接口
        :param prompt: 用户输入
        :param system_prompt: 系统提示词
        :param temperature: 温度参数
        :param max_tokens: 最大token数
        :return: 模型回复
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self._call(messages, temperature=temperature, max_tokens=max_tokens)

    def summarize_news(self, news_content: str, max_length: int = 100) -> Optional[str]:
        """
        生成新闻摘要（使用 qwen-plus 模型）
        :param news_content: 新闻内容
        :param max_length: 摘要最大长度
        :return: 新闻摘要
        """
        system_prompt = f"""你是一位专业的财经新闻分析师。请根据提供的新闻内容，生成简洁的摘要。
要求：
1. 摘要应该突出新闻的核心信息
2. 如果涉及政策或数据，需要提取关键数字
3. 语言简洁专业，不超过{max_length}字
4. 只返回摘要内容，不要有任何额外说明"""

        prompt = f"请为以下新闻生成摘要：\n\n{news_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # 使用 qwen-plus 模型进行新闻摘要
        return self._call(
            messages,
            temperature=0.3,
            max_tokens=500,
            model=DASHSCOPE_MODEL_SUMMARY,
        )

    def analyze_news_sentiment(
        self, news_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        分析新闻情感倾向和相关板块
        :param news_content: 新闻内容
        :return: {"sentiment": "positive/negative/neutral", "related_sectors": ["板块1", "板块2"], "importance": 1-5}
        """
        system_prompt = """你是一位专业的财经分析师。请分析以下新闻的情感倾向、相关板块和重要性。

请严格按照以下JSON格式返回，不要有任何额外说明：
{
    "sentiment": "positive/negative/neutral",
    "related_sectors": ["相关板块1", "相关板块2"],
    "importance": 重要性评分(1-5),
    "reason": "简短分析理由"
}

情感判断标准：
- positive: 利好消息，如政策支持、业绩增长、行业利好
- negative: 利空消息，如政策收紧、风险预警、负面事件
- neutral: 中性消息，如数据发布、人事变动等

重要性评分标准：
- 5: 重大政策发布、央行利率决议等
- 4: 重要部门公告、重大经济数据
- 3: 行业政策、普通经济数据
- 2: 一般性新闻
- 1: 轻微影响的消息"""

        prompt = f"请分析以下新闻：\n\n{news_content}"

        # 使用 qwen-plus 模型进行情感分析
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        result = self._call(
            messages,
            temperature=0.2,
            max_tokens=500,
            model=DASHSCOPE_MODEL_SUMMARY,  # 使用 qwen-plus
        )

        if result:
            try:
                # 尝试提取JSON内容
                result = result.strip()
                if result.startswith("```"):
                    # 移除代码块标记
                    lines = result.split("\n")
                    result = "\n".join(lines[1:-1])
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse sentiment analysis result: {e}")
                return None
        return None

    def generate_investment_recommendation(
        self,
        news_list: List[Dict[str, str]],
        market_trends: Dict[str, Any] = None,
    ) -> Optional[str]:
        """
        根据新闻和市场趋势生成投资建议
        :param news_list: 新闻列表 [{"title": "...", "content": "...", "source": "..."}]
        :param market_trends: 市场趋势数据
        :return: 投资建议文本
        """
        system_prompt = """你是一位专业的投资顾问。请根据提供的最新新闻和市场趋势，给出投资建议。

要求：
1. 分析当前市场环境和主要风险
2. 识别潜在的投资机会
3. 推荐具体的投资方向（如特定板块、行业）
4. 建议应该客观专业，同时提示风险
5. 不要推荐具体的股票代码

请用以下格式输出：
## 市场分析
（当前市场环境分析）

## 投资机会
（根据新闻识别的投资机会）

## 推荐方向
（推荐的投资板块或行业）

## 风险提示
（需要关注的风险因素）"""

        # 构建新闻摘要
        news_text = "\n".join(
            [
                f"- [{item.get('source', '未知')}] {item.get('title', '')}: {item.get('content', '')[:200]}"
                for item in news_list[:10]  # 最多取10条新闻
            ]
        )

        # 构建市场趋势文本
        trends_text = ""
        if market_trends:
            trends_text = f"\n\n市场趋势数据：\n{market_trends}"

        prompt = f"最新财经新闻：\n{news_text}{trends_text}\n\n请给出投资建议。"

        return self.chat(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=2000,
        )

    def is_configured(self) -> bool:
        """检查是否已配置API Key"""
        return self.client is not None
