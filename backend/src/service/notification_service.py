"""
通知服务 - 支持多渠道推送投资建议
支持的渠道: log（日志）, email（邮件）, sms（短信）, database（数据库/前端）
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from src.config import NOTIFY_CHANNELS

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """通知渠道基类"""

    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        pass

    @abstractmethod
    def send(self, title: str, content: str, metadata: Dict = None) -> bool:
        """
        发送通知
        :param title: 标题
        :param content: 内容
        :param metadata: 额外元数据
        :return: 是否发送成功
        """
        pass


class LogChannel(NotificationChannel):
    """日志输出渠道"""

    name = "log"

    def is_configured(self) -> bool:
        return True  # 日志始终可用

    def send(self, title: str, content: str, metadata: Dict = None) -> bool:
        logger.info("=" * 60)
        logger.info(f"📈 {title}")
        logger.info("=" * 60)
        for line in content.split("\n"):
            logger.info(line)
        logger.info("=" * 60)
        return True


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""

    name = "email"

    def __init__(self):
        from src.service.email_service import EmailService

        self.email_service = EmailService()

    def is_configured(self) -> bool:
        return self.email_service.is_configured()

    def send(self, title: str, content: str, metadata: Dict = None) -> bool:
        date_str = metadata.get("date", datetime.now().strftime("%Y年%m月%d日"))
        return self.email_service.send_investment_advice(content, date_str)


class SMSChannel(NotificationChannel):
    """短信通知渠道（阿里云）"""

    name = "sms"

    def __init__(self):
        from src.config import (
            SMS_ACCESS_KEY_ID,
            SMS_ACCESS_KEY_SECRET,
            SMS_PHONE_NUMBERS,
            SMS_SIGN_NAME,
            SMS_TEMPLATE_CODE,
        )

        self.access_key_id = SMS_ACCESS_KEY_ID
        self.access_key_secret = SMS_ACCESS_KEY_SECRET
        self.sign_name = SMS_SIGN_NAME
        self.template_code = SMS_TEMPLATE_CODE
        self.phone_numbers = [
            p.strip() for p in SMS_PHONE_NUMBERS.split(",") if p.strip()
        ]

    def is_configured(self) -> bool:
        return (
            self.access_key_id
            and self.access_key_secret
            and self.sign_name
            and self.template_code
            and self.phone_numbers
        )

    def send(self, title: str, content: str, metadata: Dict = None) -> bool:
        if not self.is_configured():
            logger.warning("短信服务未配置")
            return False

        try:
            # 短信内容需要精简，只发送摘要
            summary = self._extract_summary(content)

            # 使用阿里云 SDK 发送短信
            from alibabacloud_dysmsapi20170525 import models as sms_models
            from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
            from alibabacloud_tea_openapi import models as open_api_models

            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )
            config.endpoint = "dysmsapi.aliyuncs.com"
            client = DysmsapiClient(config)

            for phone in self.phone_numbers:
                request = sms_models.SendSmsRequest(
                    phone_numbers=phone,
                    sign_name=self.sign_name,
                    template_code=self.template_code,
                    template_param=json.dumps({"content": summary[:70]}),  # 短信模板变量
                )
                response = client.send_sms(request)
                if response.body.code == "OK":
                    logger.info(f"短信发送成功: {phone}")
                else:
                    logger.warning(f"短信发送失败: {phone}, {response.body.message}")

            return True

        except ImportError:
            logger.warning("短信服务需要安装 alibabacloud-dysmsapi20170525 包")
            return False
        except Exception as e:
            logger.error(f"短信发送失败: {e}")
            return False

    def _extract_summary(self, content: str) -> str:
        """提取内容摘要（短信有长度限制）"""
        # 尝试提取推荐基金类型部分
        if "推荐基金类型" in content:
            start = content.find("推荐基金类型")
            end = content.find("###", start + 1)
            if end == -1:
                end = start + 200
            summary = content[start:end].strip()
            return summary[:70]  # 限制长度

        # 否则返回前70个字符
        return content[:70].replace("\n", " ")


class DatabaseChannel(NotificationChannel):
    """数据库存储渠道（用于前端展示）"""

    name = "database"

    def is_configured(self) -> bool:
        return True  # 数据库始终可用

    def send(self, title: str, content: str, metadata: Dict = None) -> bool:
        try:
            import asyncio

            from src.infrastructure.db.database import get_db_session
            from src.infrastructure.db.pgsql import InvestmentAdvice

            async def save_advice():
                async with get_db_session() as session:
                    date_str = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
                    # 转换日期格式
                    if "年" in date_str:
                        date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")

                    # 生成摘要
                    summary = self._generate_summary(content)

                    advice = InvestmentAdvice(
                        date=date_str,
                        title=title,
                        content=content,
                        summary=summary,
                    )
                    session.add(advice)

            # 运行异步保存
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在异步上下文中，创建任务
                asyncio.create_task(save_advice())
            except RuntimeError:
                # 如果不在异步上下文中，使用 run
                asyncio.run(save_advice())

            logger.info(f"投资建议已保存到数据库")
            return True

        except Exception as e:
            logger.error(f"保存投资建议到数据库失败: {e}")
            return False

    def _generate_summary(self, content: str) -> str:
        """生成摘要"""
        # 提取推荐部分
        lines = []
        in_recommend = False
        for line in content.split("\n"):
            if "推荐基金类型" in line or "推荐方向" in line:
                in_recommend = True
            elif in_recommend:
                if line.startswith("###"):
                    break
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    lines.append(line.strip())

        if lines:
            return "\n".join(lines[:5])  # 最多5条推荐
        return content[:200]


class NotificationService:
    """通知服务 - 管理所有通知渠道"""

    def __init__(self):
        # 解析配置的渠道
        self.enabled_channels = [
            ch.strip().lower() for ch in NOTIFY_CHANNELS.split(",") if ch.strip()
        ]

        # 初始化所有渠道
        self.channels: Dict[str, NotificationChannel] = {
            "log": LogChannel(),
            "email": EmailChannel(),
            "sms": SMSChannel(),
            "database": DatabaseChannel(),
        }

        logger.info(f"通知服务初始化，启用渠道: {self.enabled_channels}")

    def get_enabled_channels(self) -> List[str]:
        """获取已启用的渠道列表"""
        return self.enabled_channels

    def get_channel_status(self) -> Dict[str, Dict]:
        """获取各渠道状态"""
        status = {}
        for name, channel in self.channels.items():
            status[name] = {
                "enabled": name in self.enabled_channels,
                "configured": channel.is_configured(),
            }
        return status

    def send(
        self,
        title: str,
        content: str,
        channels: List[str] = None,
        metadata: Dict = None,
    ) -> Dict[str, bool]:
        """
        发送通知到指定渠道
        :param title: 标题
        :param content: 内容
        :param channels: 指定渠道列表，为空则使用配置的渠道
        :param metadata: 额外元数据
        :return: 各渠道发送结果
        """
        target_channels = channels or self.enabled_channels
        results = {}

        for channel_name in target_channels:
            if channel_name not in self.channels:
                logger.warning(f"未知的通知渠道: {channel_name}")
                results[channel_name] = False
                continue

            channel = self.channels[channel_name]

            if not channel.is_configured():
                logger.warning(f"通知渠道 {channel_name} 未配置，跳过")
                results[channel_name] = False
                continue

            try:
                success = channel.send(title, content, metadata or {})
                results[channel_name] = success
                if success:
                    logger.info(f"通知发送成功: {channel_name}")
                else:
                    logger.warning(f"通知发送失败: {channel_name}")
            except Exception as e:
                logger.error(f"通知发送异常: {channel_name}, {e}")
                results[channel_name] = False

        return results

    def send_investment_advice(self, advice: str, date_str: str = None) -> Dict[str, bool]:
        """
        发送投资建议（便捷方法）
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y年%m月%d日")

        title = f"每日投资建议 - {date_str}"
        metadata = {"date": date_str}

        return self.send(title, advice, metadata=metadata)
