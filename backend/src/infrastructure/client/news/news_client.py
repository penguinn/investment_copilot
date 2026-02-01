"""
新闻采集客户端
支持：财联社、东方财富、央行、证监会、发改委、统计局、工信部
"""

import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class NewsClient:
    """新闻采集客户端"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ==================== 通用方法 ====================

    def _fetch_article_content(self, url: str, source: str) -> Optional[str]:
        """
        爬取文章详情页内容
        :param url: 文章URL
        :param source: 来源（用于选择解析规则）
        :return: 文章正文内容
        """
        if not url:
            return None

        try:
            resp = self.session.get(url, timeout=10)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            content = None

            if source == "eastmoney":
                # 东方财富公告/新闻详情（多种页面结构）
                content_div = (
                    soup.select_one(".detail-body")
                    or soup.select_one("#ContentBody")
                    or soup.select_one(".newsContent")
                    or soup.select_one("#topNewsCon")
                    or soup.select_one(".article-content")
                    or soup.select_one(".Body")
                )
                if content_div:
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            elif source == "ndrc":
                # 发改委文章详情
                content_div = soup.select_one(".TRS_Editor") or soup.select_one(
                    ".article-content"
                )
                if content_div:
                    # 移除脚本和样式
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            elif source == "stats":
                # 统计局文章详情
                content_div = soup.select_one(".TRS_Editor") or soup.select_one(
                    ".center_content"
                )
                if content_div:
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            elif source == "pbc":
                # 央行文章详情
                content_div = (
                    soup.select_one("#zoom")
                    or soup.select_one(".TRS_Editor")
                    or soup.select_one(".content")
                )
                if content_div:
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            elif source == "csrc":
                # 证监会文章详情
                content_div = (
                    soup.select_one(".TRS_Editor")
                    or soup.select_one("#ContentRegion")
                    or soup.select_one(".content")
                )
                if content_div:
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            elif source == "miit":
                # 工信部文章详情
                content_div = (
                    soup.select_one(".xxgk_con")
                    or soup.select_one(".article-content")
                    or soup.select_one(".TRS_Editor")
                )
                if content_div:
                    for tag in content_div.find_all(["script", "style"]):
                        tag.decompose()
                    content = content_div.get_text(strip=True)

            # 清理内容
            if content:
                # 移除空字符（PostgreSQL 不支持 0x00）
                content = content.replace("\x00", "")
                # 移除多余空白
                content = re.sub(r"\s+", " ", content).strip()
                # 限制长度（避免存储过长内容）
                if len(content) > 5000:
                    content = content[:5000] + "..."

            return content

        except Exception as e:
            logger.debug(f"Failed to fetch article content from {url}: {e}")
            return None

    # ==================== 财联社 ====================

    def get_cls_telegraph(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取财联社电报（7x24 快讯）
        直接通过 API 获取
        """
        result = []

        try:
            # 财联社 API
            url = "https://www.cls.cn/nodeapi/updateTelegraphList"
            params = {
                "app": "CailianpressWeb",
                "os": "web",
                "sv": "8.4.6",
                "rn": limit,
            }
            headers = {
                "Referer": "https://www.cls.cn/",
            }

            resp = self.session.get(url, params=params, headers=headers, timeout=10)
            data = resp.json()

            # 财联社返回 error=0 表示成功，数据在 data.roll_data 里
            if (
                data.get("error") == 0
                and data.get("data")
                and data["data"].get("roll_data")
            ):
                for item in data["data"]["roll_data"][:limit]:
                    try:
                        content = item.get("content", "") or item.get("brief", "")
                        title = item.get("title", "") or (
                            content[:50] + "..." if len(content) > 50 else content
                        )

                        # 解析时间戳
                        ctime = item.get("ctime", 0)
                        publish_time = (
                            datetime.fromtimestamp(ctime) if ctime else datetime.now()
                        )

                        result.append(
                            {
                                "source": "cls",
                                "source_name": "财联社",
                                "title": title,
                                "content": content,
                                "category": "news",
                                "publish_time": publish_time,
                                "importance": self._calc_importance(content),
                                "related_sectors": self._extract_sectors(content),
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to parse CLS item: {e}")
                        continue

            logger.info(f"获取到 {len(result)} 条新闻 - 财联社快讯")

        except Exception as e:
            logger.error(f"Failed to fetch CLS telegraph: {e}")
            # 尝试备用方案：AKShare
            try:
                import akshare as ak

                df = ak.stock_telegraph_cls()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        time_str = str(row.get("发布时间", ""))
                        try:
                            if len(time_str) <= 8:
                                today = datetime.now().strftime("%Y-%m-%d")
                                publish_time = datetime.strptime(
                                    f"{today} {time_str}", "%Y-%m-%d %H:%M:%S"
                                )
                            else:
                                publish_time = datetime.strptime(
                                    time_str, "%Y-%m-%d %H:%M:%S"
                                )
                        except:
                            publish_time = datetime.now()

                        content = str(row.get("内容", ""))
                        title = content[:50] + "..." if len(content) > 50 else content

                        result.append(
                            {
                                "source": "cls",
                                "source_name": "财联社",
                                "title": title,
                                "content": content,
                                "category": "news",
                                "publish_time": publish_time,
                                "importance": self._calc_importance(content),
                                "related_sectors": self._extract_sectors(content),
                            }
                        )
                    logger.info(f"获取到 {len(result)} 条新闻 - 财联社快讯(备用)")
            except Exception as e2:
                logger.warning(f"CLS fallback also failed: {e2}")

        return result

    # ==================== 东方财富 ====================

    def get_eastmoney_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取东方财富财经新闻（使用 7x24 快讯 API）
        """
        result = []

        try:
            # 东方财富公告/新闻 API
            url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            params = {
                "sr": "-1",
                "page_size": limit,
                "page_index": "1",
                "ann_type": "SHA,SZA,BJA",
                "client_source": "web",
                "f_node": "0",
                "s_node": "0",
            }

            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()

            if data.get("data") and data["data"].get("list"):
                for item in data["data"]["list"][:limit]:
                    try:
                        title = item.get("title", "")
                        content = item.get("digest", "") or item.get("content", "")
                        art_code = item.get("art_code", "")
                        news_url = (
                            f"https://data.eastmoney.com/notices/detail/{art_code}.html"
                            if art_code
                            else ""
                        )

                        # 如果内容为空或内容等于标题，尝试获取详情
                        if not content or content == title:
                            if news_url:
                                detail_content = self._fetch_article_content(
                                    news_url, "eastmoney"
                                )
                                if detail_content:
                                    content = detail_content
                                time.sleep(0.2)
                            if not content:
                                content = title

                        # 解析时间
                        notice_date = item.get("notice_date", "")
                        try:
                            if notice_date and len(notice_date) >= 10:
                                publish_time = datetime.strptime(
                                    notice_date[:10], "%Y-%m-%d"
                                )
                            else:
                                publish_time = datetime.now()
                        except:
                            publish_time = datetime.now()

                        result.append(
                            {
                                "source": "eastmoney",
                                "source_name": "东方财富",
                                "title": title,
                                "content": content,
                                "url": news_url,
                                "category": "news",
                                "publish_time": publish_time,
                                "importance": self._calc_importance(title + content),
                                "related_sectors": self._extract_sectors(
                                    title + content
                                ),
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to parse EastMoney item: {e}")
                        continue

            logger.info(f"获取到 {len(result)} 条新闻 - 东方财富")

        except Exception as e:
            logger.error(f"Failed to fetch EastMoney news: {e}")
            # 尝试备用方案：AKShare
            try:
                import akshare as ak

                df = ak.stock_news_em(symbol="财经")
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get("新闻标题", ""))
                        content = str(row.get("新闻内容", title))
                        news_url = str(row.get("新闻链接", ""))
                        time_str = str(row.get("发布时间", ""))
                        try:
                            publish_time = datetime.strptime(
                                time_str, "%Y-%m-%d %H:%M:%S"
                            )
                        except:
                            publish_time = datetime.now()

                        result.append(
                            {
                                "source": "eastmoney",
                                "source_name": "东方财富",
                                "title": title,
                                "content": content,
                                "url": news_url,
                                "category": "news",
                                "publish_time": publish_time,
                                "importance": self._calc_importance(title + content),
                                "related_sectors": self._extract_sectors(
                                    title + content
                                ),
                            }
                        )
                    logger.info(f"获取到 {len(result)} 条新闻 - 东方财富(备用)")
            except Exception as e2:
                logger.warning(f"EastMoney fallback also failed: {e2}")

        return result

    # ==================== 央行 ====================

    def get_pbc_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取央行公告/新闻
        """
        result = []

        # 央行新闻发布
        try:
            url = "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html"
            resp = self.session.get(url, timeout=10)
            resp.encoding = "utf-8"

            soup = BeautifulSoup(resp.text, "html.parser")

            # 央行页面结构：.newslist_style 为 font 内包 a，不是 ul li
            items = soup.select(".newslist_style a")

            for item in items[:limit]:
                try:
                    title = item.get_text(strip=True)
                    href = item.get("href", "")

                    # 处理相对链接
                    if href.startswith("./"):
                        href = (
                            "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/"
                            + href[2:]
                        )
                    elif not href.startswith("http"):
                        href = "http://www.pbc.gov.cn" + href

                    # 从 URL 解析日期，如 .../2026012917370637541/index.html
                    publish_time = datetime.now()
                    match = re.search(r"/(\d{8})\d+", href)
                    if match:
                        try:
                            publish_time = datetime.strptime(match.group(1), "%Y%m%d")
                        except ValueError:
                            pass

                    # 尝试获取详情内容
                    content = self._fetch_article_content(href, "pbc")
                    if not content:
                        content = title

                    result.append(
                        {
                            "source": "pbc",
                            "source_name": "中国人民银行",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "policy",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(title, is_policy=True),
                            "related_sectors": self._extract_sectors(title),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse PBC item: {e}")
                    continue

            logger.info(f"获取到 {len(result)} 条新闻 - 中国人民银行")

        except Exception as e:
            logger.error(f"Failed to fetch PBC news: {e}")

        return result

    # ==================== 证监会 ====================

    def get_csrc_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取证监会公告/新闻
        """
        result = []

        try:
            # 证监会新闻发布
            url = "http://www.csrc.gov.cn/csrc/c100028/common_list.shtml"
            resp = self.session.get(url, timeout=10)
            resp.encoding = "utf-8"

            soup = BeautifulSoup(resp.text, "html.parser")

            # 证监会页面结构：列表在 ul.list 下
            items = soup.select("ul.list li") or soup.select(".list li")

            for item in items[:limit]:
                try:
                    link = item.find("a")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get("href", "")

                    if not href.startswith("http"):
                        href = "http://www.csrc.gov.cn" + href

                    # 解析时间
                    date_span = item.find("span") or item.find(class_="date")
                    if date_span:
                        date_str = date_span.get_text(strip=True)
                        try:
                            publish_time = datetime.strptime(date_str, "%Y-%m-%d")
                        except:
                            publish_time = datetime.now()
                    else:
                        publish_time = datetime.now()

                    # 尝试获取详情内容
                    content = self._fetch_article_content(href, "csrc")
                    if not content:
                        content = title

                    result.append(
                        {
                            "source": "csrc",
                            "source_name": "中国证监会",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "policy",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(title, is_policy=True),
                            "related_sectors": self._extract_sectors(title),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse CSRC item: {e}")
                    continue

            logger.info(f"获取到 {len(result)} 条新闻 - 中国证监会")

        except Exception as e:
            logger.error(f"Failed to fetch CSRC news: {e}")

        return result

    # ==================== 发改委 ====================

    def get_ndrc_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取发改委新闻/政策
        """
        result = []

        try:
            # 发改委新闻
            url = "https://www.ndrc.gov.cn/xwdt/xwfb/index.html"
            resp = self.session.get(url, timeout=10)
            resp.encoding = "utf-8"

            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select(".list_con li") or soup.select(".u-list li")

            for item in items[:limit]:
                try:
                    link = item.find("a")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get("href", "")

                    if href.startswith("./"):
                        href = "https://www.ndrc.gov.cn/xwdt/xwfb/" + href[2:]
                    elif not href.startswith("http"):
                        href = "https://www.ndrc.gov.cn" + href

                    # 解析时间
                    date_span = item.find("span") or item.find(class_="date")
                    if date_span:
                        date_str = date_span.get_text(strip=True)
                        try:
                            publish_time = datetime.strptime(date_str, "%Y/%m/%d")
                        except:
                            try:
                                publish_time = datetime.strptime(date_str, "%Y-%m-%d")
                            except:
                                publish_time = datetime.now()
                    else:
                        publish_time = datetime.now()

                    # 爬取详情页内容
                    content = self._fetch_article_content(href, "ndrc")
                    if not content:
                        content = title
                    time.sleep(0.3)  # 避免请求过快

                    result.append(
                        {
                            "source": "ndrc",
                            "source_name": "国家发改委",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "policy",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(
                                title + content, is_policy=True
                            ),
                            "related_sectors": self._extract_sectors(title + content),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse NDRC item: {e}")
                    continue

            logger.info(f"获取到 {len(result)} 条新闻 - 发改委")

        except Exception as e:
            logger.error(f"Failed to fetch NDRC news: {e}")

        return result

    # ==================== 统计局 ====================

    def get_stats_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取国家统计局数据发布
        """
        result = []

        try:
            # 统计局数据发布
            url = "http://www.stats.gov.cn/sj/zxfb/index.html"
            resp = self.session.get(url, timeout=10)
            resp.encoding = "utf-8"

            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select(".list-content li") or soup.select(".center_list li")

            for item in items[:limit]:
                try:
                    link = item.find("a")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get("href", "")

                    if href.startswith("./"):
                        href = "http://www.stats.gov.cn/sj/zxfb/" + href[2:]
                    elif not href.startswith("http"):
                        href = "http://www.stats.gov.cn" + href

                    # 解析时间
                    date_span = item.find("span") or item.find(class_="date")
                    if date_span:
                        date_str = date_span.get_text(strip=True)
                        try:
                            publish_time = datetime.strptime(date_str, "%Y-%m-%d")
                        except:
                            publish_time = datetime.now()
                    else:
                        publish_time = datetime.now()

                    # 爬取详情页内容
                    content = self._fetch_article_content(href, "stats")
                    if not content:
                        content = title
                    time.sleep(0.3)  # 避免请求过快

                    result.append(
                        {
                            "source": "stats",
                            "source_name": "国家统计局",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "data",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(
                                title + content, is_policy=True
                            ),
                            "related_sectors": self._extract_sectors(title + content),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse Stats item: {e}")
                    continue

            logger.info(f"获取到 {len(result)} 条新闻 - 国家统计局")

        except Exception as e:
            logger.error(f"Failed to fetch Stats news: {e}")

        return result

    # ==================== 工信部 ====================

    def _get_miit_news_via_playwright(
        self, url: str, limit: int
    ) -> List[Dict[str, Any]]:
        """
        通过无头浏览器获取工信部列表页渲染后的 HTML 并解析。
        需安装: pip install playwright && playwright install chromium
        """
        result = []
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.debug("playwright 未安装，跳过工信部无头浏览器采集")
            return result

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=HEADERS["User-Agent"],
                    locale="zh-CN",
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # 等待 JS 渲染出的列表链接出现
                page.wait_for_selector(
                    ".clist_con a[href*='index.html'], .clist_con ul li a",
                    timeout=20000,
                )
                time.sleep(1)  # 再等片刻确保列表完整
                html = page.content()
                context.close()
                browser.close()

            soup = BeautifulSoup(html, "html.parser")
            # 渲染后列表在 .clist_con 内，链接或 li
            container = soup.select_one(".clist_con")
            if not container:
                return result
            items = container.select("ul li") or container.select("li")
            if not items:
                links = container.select("a[href*='index.html']")
                for link in links[:limit]:
                    href = link.get("href", "")
                    if not href or "javascript" in href:
                        continue
                    title = link.get_text(strip=True)
                    if not title or len(title) < 2:
                        continue
                    if href.startswith("./"):
                        href = "https://www.miit.gov.cn/xwdt/gxdt/ldhd/" + href[2:]
                    elif not href.startswith("http"):
                        href = "https://www.miit.gov.cn" + href
                    date_span = link.find_parent("li")
                    if date_span:
                        date_el = date_span.find("span") or date_span.find(
                            class_="date"
                        )
                        if date_el:
                            try:
                                publish_time = datetime.strptime(
                                    date_el.get_text(strip=True), "%Y-%m-%d"
                                )
                            except ValueError:
                                publish_time = datetime.now()
                        else:
                            publish_time = datetime.now()
                    else:
                        publish_time = datetime.now()

                    # 尝试获取详情内容
                    content = self._fetch_article_content(href, "miit")
                    if not content:
                        content = title

                    result.append(
                        {
                            "source": "miit",
                            "source_name": "工信部",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "policy",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(title, is_policy=True),
                            "related_sectors": self._extract_sectors(title),
                        }
                    )
                return result

            for item in items[:limit]:
                try:
                    link = item.find("a")
                    if not link:
                        continue
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    if not href or "javascript" in href:
                        continue
                    if href.startswith("./"):
                        href = "https://www.miit.gov.cn/xwdt/gxdt/ldhd/" + href[2:]
                    elif not href.startswith("http"):
                        href = "https://www.miit.gov.cn" + href
                    date_span = item.find("span") or item.find(class_="date")
                    if date_span:
                        date_str = date_span.get_text(strip=True)
                        try:
                            publish_time = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            publish_time = datetime.now()
                    else:
                        publish_time = datetime.now()

                    # 尝试获取详情内容
                    content = self._fetch_article_content(href, "miit")
                    if not content:
                        content = title

                    result.append(
                        {
                            "source": "miit",
                            "source_name": "工信部",
                            "title": title,
                            "content": content,
                            "url": href,
                            "category": "policy",
                            "publish_time": publish_time,
                            "importance": self._calc_importance(title, is_policy=True),
                            "related_sectors": self._extract_sectors(title),
                        }
                    )
                except Exception as e:
                    logger.debug(f"Failed to parse MIIT item: {e}")
                    continue
            return result
        except Exception as e:
            logger.warning(f"工信部无头浏览器采集失败: {e}")
            return result

    def get_miit_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取工信部新闻/政策。
        列表页由 JS 动态渲染，使用无头浏览器（Playwright）采集。
        安装: pip install playwright && playwright install chromium
        关闭采集（省内存）: 环境变量 MIIT_USE_PLAYWRIGHT=0 或 false
        """
        use_playwright = os.environ.get("MIIT_USE_PLAYWRIGHT", "1").lower() in (
            "1",
            "true",
            "yes",
        )
        if not use_playwright:
            logger.info("工信部采集已关闭 (MIIT_USE_PLAYWRIGHT=0) - 获取到 0 条新闻")
            return []

        url = "https://www.miit.gov.cn/xwdt/gxdt/ldhd/index.html"
        result = self._get_miit_news_via_playwright(url, limit)

        logger.info(f"获取到 {len(result)} 条新闻 - 工信部")
        return result

    # ==================== 综合获取 ====================

    def get_all_news(self, limit_per_source: int = 20) -> List[Dict[str, Any]]:
        """获取所有来源的新闻"""
        all_news = []

        # 财联社快讯（最重要）
        all_news.extend(self.get_cls_telegraph(limit_per_source))
        time.sleep(0.5)

        # 东方财富
        all_news.extend(self.get_eastmoney_news(limit_per_source))
        time.sleep(0.5)

        # 官方来源
        all_news.extend(self.get_pbc_news(limit_per_source))
        time.sleep(0.5)

        all_news.extend(self.get_csrc_news(limit_per_source))
        time.sleep(0.5)

        all_news.extend(self.get_ndrc_news(limit_per_source))
        time.sleep(0.5)

        all_news.extend(self.get_stats_news(limit_per_source))
        time.sleep(0.5)

        all_news.extend(self.get_miit_news(limit_per_source))

        # 按发布时间排序
        all_news.sort(key=lambda x: x.get("publish_time", datetime.min), reverse=True)

        logger.info(f"Total fetched {len(all_news)} news from all sources")
        return all_news

    # ==================== 辅助方法 ====================

    def _calc_importance(self, text: str, is_policy: bool = False) -> int:
        """计算新闻重要性（1-5）"""
        importance = 2 if is_policy else 1

        # 关键词权重
        high_keywords = [
            "降准",
            "降息",
            "加息",
            "央行",
            "货币政策",
            "利率",
            "IPO",
            "退市",
            "停牌",
            "暴涨",
            "暴跌",
            "涨停",
            "跌停",
            "重大",
            "紧急",
            "突发",
            "首次",
            "历史",
            "GDP",
            "CPI",
            "PMI",
            "就业",
            "失业",
            "战争",
            "制裁",
            "贸易战",
            "关税",
        ]

        medium_keywords = [
            "政策",
            "改革",
            "规划",
            "意见",
            "通知",
            "融资",
            "并购",
            "重组",
            "股权",
            "新能源",
            "芯片",
            "半导体",
            "人工智能",
            "AI",
            "房地产",
            "楼市",
            "医药",
            "银行",
        ]

        text_lower = text.lower()

        for kw in high_keywords:
            if kw in text:
                importance = min(importance + 2, 5)
                break

        for kw in medium_keywords:
            if kw in text:
                importance = min(importance + 1, 5)
                break

        return importance

    def _extract_sectors(self, text: str) -> str:
        """从文本中提取相关板块"""
        sector_keywords = {
            "银行": ["银行", "信贷", "存款", "贷款"],
            "证券": ["证券", "券商", "股市", "交易所"],
            "保险": ["保险", "寿险", "财险"],
            "房地产": ["房地产", "楼市", "住房", "土地"],
            "新能源": ["新能源", "光伏", "风电", "储能", "电池"],
            "汽车": ["汽车", "新能源车", "电动车"],
            "半导体": ["半导体", "芯片", "集成电路"],
            "医药": ["医药", "医疗", "药品", "疫苗"],
            "消费": ["消费", "零售", "白酒", "食品"],
            "军工": ["军工", "国防", "军事", "武器"],
            "科技": ["科技", "人工智能", "AI", "互联网"],
            "农业": ["农业", "粮食", "养殖", "畜牧"],
        }

        found_sectors = []
        for sector, keywords in sector_keywords.items():
            for kw in keywords:
                if kw in text:
                    found_sectors.append(sector)
                    break

        return ",".join(found_sectors) if found_sectors else ""
