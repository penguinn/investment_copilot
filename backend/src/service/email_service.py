"""
邮件发送服务
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from src.config import (
    EMAIL_ENABLED,
    EMAIL_FROM,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PASSWORD,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_USER,
    EMAIL_TO,
)

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务"""

    def __init__(self):
        self.enabled = EMAIL_ENABLED
        self.smtp_host = EMAIL_SMTP_HOST
        self.smtp_port = EMAIL_SMTP_PORT
        self.smtp_user = EMAIL_SMTP_USER
        self.smtp_password = EMAIL_SMTP_PASSWORD
        self.from_addr = EMAIL_FROM or EMAIL_SMTP_USER
        self.to_addrs = [addr.strip() for addr in EMAIL_TO.split(",") if addr.strip()]

    def is_configured(self) -> bool:
        """检查邮件是否已配置"""
        return (
            self.enabled
            and self.smtp_host
            and self.smtp_user
            and self.smtp_password
            and self.to_addrs
        )

    def send_email(
        self,
        subject: str,
        content: str,
        to_addrs: Optional[List[str]] = None,
        html: bool = True,
    ) -> bool:
        """
        发送邮件
        :param subject: 邮件主题
        :param content: 邮件内容
        :param to_addrs: 收件人列表，为空则使用配置的默认收件人
        :param html: 是否为 HTML 格式
        :return: 是否发送成功
        """
        if not self.is_configured():
            logger.warning("邮件服务未配置，跳过发送")
            return False

        recipients = to_addrs or self.to_addrs
        if not recipients:
            logger.warning("没有收件人，跳过发送")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(recipients)

            # 添加内容
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(content, content_type, "utf-8"))

            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_addr, recipients, msg.as_string())

            logger.info(f"邮件发送成功: {subject} -> {recipients}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_investment_advice(self, advice: str, date_str: str) -> bool:
        """
        发送每日投资建议邮件
        :param advice: 投资建议内容
        :param date_str: 日期字符串
        """
        subject = f"📈 每日投资建议 - {date_str}"

        # 将 Markdown 格式转换为简单的 HTML
        html_content = self._markdown_to_html(advice, date_str)

        return self.send_email(subject, html_content, html=True)

    def _markdown_to_html(self, markdown_text: str, date_str: str) -> str:
        """将 Markdown 格式的投资建议转换为 HTML"""
        import re

        # 基本的 Markdown 转 HTML
        html = markdown_text

        # 标题转换
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # 粗体
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # 列表项
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # 换行
        html = html.replace("\n\n", "</p><p>")
        html = html.replace("\n", "<br>")

        # 包装成完整的 HTML
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 2px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34a853;
            margin-top: 25px;
        }}
        h3 {{
            color: #ea4335;
            margin-top: 20px;
        }}
        li {{
            margin: 8px 0;
            padding-left: 5px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .date {{
            color: #666;
            font-size: 14px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 10px 15px;
            margin-top: 20px;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 每日投资建议</h1>
            <p class="date">{date_str}</p>
        </div>
        <div class="content">
            <p>{html}</p>
        </div>
        <div class="disclaimer">
            ⚠️ <strong>风险提示</strong>：以上内容仅供参考，不构成投资建议。投资有风险，入市需谨慎。
        </div>
        <div class="footer">
            <p>此邮件由 Investment Copilot 自动生成</p>
        </div>
    </div>
</body>
</html>
"""
