import json
import logging
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view

from ..model import GoldIndex, MarketIndex, StockIndex, StockQuote
from .market_controller import MARKET_INDICES

logger = logging.getLogger(__name__)

# 市场指数映射
MARKET_MAPPING = {
    # A股市场
    "CN": {
        "shangzheng": MARKET_INDICES["CN"]["SSE"]["symbol"],
        "shenzhen": MARKET_INDICES["CN"]["SZSE"]["symbol"],
        "chuangye": MARKET_INDICES["CN"]["ChiNext"]["symbol"],
    },
    # 港股市场
    "HK": {
        "hsi": MARKET_INDICES["HK"]["HSI"]["symbol"],
        "hscei": MARKET_INDICES["HK"]["HSCEI"]["symbol"],
        "hstech": MARKET_INDICES["HK"]["HSTECH"]["symbol"],
    },
    # 美股市场
    "US": {
        "dji": MARKET_INDICES["US"]["DJI"]["symbol"],
        "nasdaq": MARKET_INDICES["US"]["IXIC"]["symbol"],
        "sp500": MARKET_INDICES["US"]["SPX"]["symbol"],
    },
}

# 市场指数名称映射
MARKET_NAMES = {
    # A股市场
    "CN": {
        "shangzheng": MARKET_INDICES["CN"]["SSE"]["name"],
        "shenzhen": MARKET_INDICES["CN"]["SZSE"]["name"],
        "chuangye": MARKET_INDICES["CN"]["ChiNext"]["name"],
    },
    # 港股市场
    "HK": {
        "hsi": MARKET_INDICES["HK"]["HSI"]["name"],
        "hscei": MARKET_INDICES["HK"]["HSCEI"]["name"],
        "hstech": MARKET_INDICES["HK"]["HSTECH"]["name"],
    },
    # 美股市场
    "US": {
        "dji": MARKET_INDICES["US"]["DJI"]["name"],
        "nasdaq": MARKET_INDICES["US"]["IXIC"]["name"],
        "sp500": MARKET_INDICES["US"]["SPX"]["name"],
    },
}

# 市场指数配置
MARKET_INDICES = {
    # A股市场
    "CN": {
        "SSE": {"symbol": "sh000001", "name": "上证指数"},
        "SZSE": {"symbol": "sz399001", "name": "深证成指"},
        "ChiNext": {"symbol": "sz399006", "name": "创业板指"},
    },
    # 港股市场
    "HK": {
        "HSI": {"symbol": "hkHSI", "name": "恒生指数"},
        "HSCEI": {"symbol": "hkHSCEI", "name": "恒生国企指数"},
        "HSTECH": {"symbol": "hkHSTECH", "name": "恒生科技指数"},
    },
    # 美股市场
    "US": {
        "DJI": {"symbol": "DJI", "name": "道琼斯工业指数"},
        "IXIC": {"symbol": "IXIC", "name": "纳斯达克综合指数"},
        "SPX": {"symbol": "SPX", "name": "标普500指数"},
    },
}

# 黄金指数配置
GOLD_INDICES = {
    "AU9999": {"symbol": "AU9999", "name": "黄金9999"},
    "XAU": {"symbol": "XAU", "name": "伦敦金"},
}


@api_view(["GET"])
def stock_index(request, market, index_code):
    try:
        k_type = request.GET.get("type", "min")

        # 构建缓存key
        cache_key = f"stock_index:{market}:{index_code}:{k_type}"

        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Retrieved data from cache for {cache_key}")
            return JsonResponse(json.loads(cached_data), safe=False)

        start_time = request.GET.get("start_time")
        logger.info(
            f"Fetching {market}:{index_code} data with type {k_type}, start_time {start_time}"
        )

        if market not in MARKET_MAPPING or index_code not in MARKET_MAPPING[market]:
            return JsonResponse({"error": "Invalid market or index code"}, status=400)

        symbol = MARKET_MAPPING[market][index_code]

        # 根据不同的市场和K线类型获取数据
        if market == "CN":
            df = get_cn_market_data(symbol, k_type)
        elif market == "HK":
            df = get_hk_market_data(symbol, k_type)
        elif market == "US":
            df = get_us_market_data(symbol, k_type)
        else:
            return JsonResponse({"error": "Unsupported market"}, status=400)

        if df.empty:
            return JsonResponse({"error": "No data available"}, status=404)

        # 转换数据格式
        data = format_market_data(df, market, k_type)
        logger.info(f"Successfully formatted {len(data)} data points")

        # 数据获取后，存入数据库
        @transaction.atomic
        def save_to_db(data_points):
            for point in data_points:
                StockQuote.objects.create(
                    symbol=MARKET_MAPPING[market][index_code],
                    time=datetime.strptime(
                        point["time"], "%Y%m%d %H:%M" if k_type == "min" else "%Y-%m-%d"
                    ),
                    current=point["close"],
                    change=0,  # 需要计算变化值
                    change_percent=0,  # 需要计算变化百分比
                )

        # 在缓存数据之前保存到数据库
        save_to_db(data)

        # 在返回数据前，将数据存入缓存
        # 对于分钟级数据设置较短的过期时间，日K等数据可以设置较长的过期时间
        ttl = 60 if k_type == "min" else 3600  # 分钟数据缓存1分钟，其他数据缓存1小时
        cache.set(cache_key, json.dumps(data), timeout=ttl)

        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f"Error in stock_index view: {str(e)}", exc_info=True)
        return JsonResponse(
            {"error": str(e), "detail": "Failed to fetch stock data"}, status=500
        )


@api_view(["GET"])
def stock_quotes(request, market):
    """获取指定市场的所有指数行情"""
    try:
        # 构建缓存key
        cache_key = f"stock_quotes:{market}"

        # 尝试从缓存获取数据
        cached_quotes = cache.get(cache_key)
        if cached_quotes:
            logger.info("Retrieved quotes from cache")
            return JsonResponse(json.loads(cached_quotes))

        if market not in MARKET_MAPPING:
            return JsonResponse({"error": "Invalid market"}, status=400)

        quotes = {}

        def get_latest_quote(market, symbol, code):
            try:
                if market == "CN":
                    df = ak.stock_zh_index_spot_sina()
                elif market == "HK":
                    df = ak.stock_hk_index_spot_em()
                elif market == "US":
                    df = ak.stock_us_spot_em()
                else:
                    return None

                # 找到对应指数的数据
                index_data = df[
                    df["代码"].str.contains(symbol.replace("sh", "").replace("sz", ""))
                ].iloc[0]

                # 处理不同的列名格式
                price = float(
                    index_data.get(
                        "当前价", index_data.get("最新价", index_data.get("price", 0))
                    )
                )
                change = float(index_data.get("涨跌额", index_data.get("change", 0)))
                change_percent = float(
                    index_data.get("涨跌幅", index_data.get("pct_chg", 0))
                )

                return {
                    "name": MARKET_NAMES[market][code],
                    "current": price,
                    "change": change,
                    "changePercent": change_percent,
                }
            except Exception as e:
                logger.error(f"Error getting data for {market}:{code}: {str(e)}")
                return None

        # 获取市场所有指数的行情
        for code, symbol in MARKET_MAPPING[market].items():
            quote = get_latest_quote(market, symbol, code)
            if quote:
                quotes[code] = quote
            else:
                quotes[code] = {
                    "name": MARKET_NAMES[market][code],
                    "current": 0,
                    "change": 0,
                    "changePercent": 0,
                }
            logger.info(f"Processed {market}:{code} quote: {quotes[code]}")

        # 在返回数据前，将数据存入缓存
        cache.set(cache_key, json.dumps(quotes), timeout=30)  # 缓存30秒

        return JsonResponse(quotes)
    except Exception as e:
        logger.error(f"Error in stock_quotes view: {str(e)}", exc_info=True)
        return JsonResponse(
            {"error": str(e), "detail": "Failed to fetch stock quotes"}, status=500
        )


@api_view(["GET"])
def market_index(request, market, index_code):
    """
    获取指定市场的指数数据
    :param market: 市场代码 (CN/HK/US)
    :param index_code: 指数代码
    :query chart_type: 图表类型 (kline/trend)
    :query period: 时间周期 (1min/5min/15min/30min/60min/day/week/month)
    :query limit: 获取数据条数，默认为 100 条
    """
    try:
        chart_type = request.GET.get("chart_type", "kline")  # kline 或 trend
        period = request.GET.get("period", "day")  # 默认日K
        limit = int(request.GET.get("limit", "100"))  # 默认100条数据

        # 验证参数
        if chart_type not in ["kline", "trend"]:
            return JsonResponse({"error": "Invalid chart type"}, status=400)

        if period not in [
            "1min",
            "5min",
            "15min",
            "30min",
            "60min",
            "day",
            "week",
            "month",
        ]:
            return JsonResponse({"error": "Invalid period"}, status=400)

        # 构建缓存key
        cache_key = f"market_index:{market}:{index_code}:{chart_type}:{period}:{limit}"

        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Retrieved data from cache for {cache_key}")
            return JsonResponse(json.loads(cached_data), safe=False)

        if market not in MARKET_INDICES or index_code not in MARKET_INDICES[market]:
            return JsonResponse({"error": "Invalid market or index code"}, status=400)

        index_info = MARKET_INDICES[market][index_code]

        # 获取原始数据
        df = get_market_data(market, index_info["symbol"], period)

        if df.empty:
            return JsonResponse({"error": "No data available"}, status=404)

        # 根据不同图表类型格式化数据
        if chart_type == "kline":
            data = format_kline_data(df, period, limit)
        else:  # trend
            data = format_trend_data(df, period, limit)

        # 保存到数据库
        save_market_data(data, market, index_info)

        # 设置缓存时间
        if period in ["1min", "5min", "15min"]:
            ttl = 60  # 1分钟
        elif period in ["30min", "60min"]:
            ttl = 300  # 5分钟
        else:
            ttl = 3600  # 1小时

        cache.set(cache_key, json.dumps(data), timeout=ttl)
        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f"Error in market_index view: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


def get_market_data(market, symbol, period):
    """
    获取市场数据
    :param market: 市场类型
    :param symbol: 指数代码
    :param period: 时间周期
    """
    try:
        if market == "CN":
            if period in ["1min", "5min", "15min", "30min", "60min"]:
                minutes = period.replace("min", "")
                return ak.index_zh_a_hist_min_em(
                    symbol=symbol.replace("sh", "").replace("sz", ""), period=minutes
                )
            elif period == "day":
                return ak.stock_zh_index_daily(symbol=symbol)
            elif period == "week":
                return ak.stock_zh_index_weekly(symbol=symbol)
            elif period == "month":
                return ak.stock_zh_index_monthly(symbol=symbol)

        elif market == "HK":
            if period in ["1min", "5min", "15min", "30min", "60min"]:
                minutes = period.replace("min", "")
                return ak.stock_hk_index_hist_min_em(symbol=symbol, period=minutes)
            else:
                return ak.stock_hk_index_daily_em(symbol=symbol)

        elif market == "US":
            if period in ["1min", "5min", "15min", "30min", "60min"]:
                minutes = period.replace("min", "")
                return ak.stock_us_index_hist_min_em(symbol=symbol, period=minutes)
            else:
                return ak.stock_us_index_daily_em(symbol=symbol)
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        raise


def format_kline_data(df, period, limit):
    """
    格式化K线图数据
    返回格式：
    {
        "time": [...],  # 时间
        "open": [...],  # 开盘价
        "high": [...],  # 最高价
        "low": [...],  # 最低价
        "close": [...], # 收盘价
        "volume": [...] # 成交量
    }
    """
    try:
        # 确保数据按时间排序
        df = df.sort_values(by=["时间" if "时间" in df.columns else "date"])
        df = df.tail(limit)  # 只取最新的 limit 条数据

        result = {
            "time": [],
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "volume": [],
        }

        for _, row in df.iterrows():
            # 处理时间
            if period in ["1min", "5min", "15min", "30min", "60min"]:
                time_str = str(row.get("时间", row.get("time", "")))
            else:
                time_str = str(row.get("date", row.get("日期", ""))).split()[0]

            result["time"].append(time_str)
            result["open"].append(float(row.get("开盘", row.get("open", 0))))
            result["high"].append(float(row.get("最高", row.get("high", 0))))
            result["low"].append(float(row.get("最低", row.get("low", 0))))
            result["close"].append(float(row.get("收盘", row.get("close", 0))))
            result["volume"].append(float(row.get("成交量", row.get("volume", 0))))

        return result
    except Exception as e:
        logger.error(f"Error formatting kline data: {str(e)}")
        raise


def format_trend_data(df, period, limit):
    """
    格式化趋势图数据
    返回格式：
    {
        "time": [...],  # 时间
        "price": [...], # 价格
        "volume": [...] # 成交量
    }
    """
    try:
        # 确保数据按时间排序
        df = df.sort_values(by=["时间" if "时间" in df.columns else "date"])
        df = df.tail(limit)  # 只取最新的 limit 条数据

        result = {"time": [], "price": [], "volume": []}

        for _, row in df.iterrows():
            # 处理时间
            if period in ["1min", "5min", "15min", "30min", "60min"]:
                time_str = str(row.get("时间", row.get("time", "")))
            else:
                time_str = str(row.get("date", row.get("日期", ""))).split()[0]

            result["time"].append(time_str)
            result["price"].append(float(row.get("收盘", row.get("close", 0))))
            result["volume"].append(float(row.get("成交量", row.get("volume", 0))))

        return result
    except Exception as e:
        logger.error(f"Error formatting trend data: {str(e)}")
        raise


@api_view(["GET"])
def gold_index(request):
    """获取黄金指数数据"""
    try:
        cache_key = "gold_indices"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(json.loads(cached_data), safe=False)

        gold_data = {}

        # 获取上海黄金交易所数据
        try:
            sh_gold_df = ak.spot_goods_gold_sge()
            for symbol, info in GOLD_INDICES.items():
                if symbol == "AU9999":
                    gold_data[symbol] = {
                        "name": info["name"],
                        "price": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "最新价"
                            ].iloc[0]
                        ),
                        "change": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "涨跌"
                            ].iloc[0]
                        ),
                        "change_percent": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "涨跌幅"
                            ].iloc[0]
                        ),
                    }
        except Exception as e:
            logger.error(f"Error fetching SGE gold data: {str(e)}")

        # 获取伦敦金数据
        try:
            london_gold_df = ak.spot_goods_gold_london()
            if "XAU" in GOLD_INDICES:
                gold_data["XAU"] = {
                    "name": GOLD_INDICES["XAU"]["name"],
                    "price": float(london_gold_df["美元价格"].iloc[0]),
                    "change": float(london_gold_df["涨跌"].iloc[0]),
                    "change_percent": float(london_gold_df["涨跌幅"].iloc[0]),
                }
        except Exception as e:
            logger.error(f"Error fetching London gold data: {str(e)}")

        # 保存到数据库
        save_gold_data(gold_data)

        # 缓存数据
        cache.set(cache_key, json.dumps(gold_data), timeout=300)  # 缓存5分钟

        return JsonResponse(gold_data, safe=False)

    except Exception as e:
        logger.error(f"Error in gold_index view: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


# 辅助函数
def get_cn_market_data(symbol, k_type):
    """获取A股市场数据"""
    if k_type == "min":
        return ak.index_zh_a_hist_min_em(
            symbol=symbol.replace("sh", "").replace("sz", "")
        )
    elif k_type == "daily":
        return ak.stock_zh_index_daily(symbol=symbol).tail(30)
    elif k_type == "weekly":
        return ak.stock_zh_index_weekly(symbol=symbol).tail(30)
    elif k_type == "monthly":
        return ak.stock_zh_index_monthly(symbol=symbol).tail(30)


def get_hk_market_data(symbol, k_type):
    """获取港股市场数据"""
    if k_type == "min":
        return ak.stock_hk_index_hist_min_em(symbol=symbol)
    else:
        return ak.stock_hk_index_daily_em(symbol=symbol).tail(30)


def get_us_market_data(symbol, k_type):
    """获取美股市场数据"""
    if k_type == "min":
        return ak.stock_us_index_hist_min_em(symbol=symbol)
    else:
        return ak.stock_us_index_daily_em(symbol=symbol).tail(30)


def format_market_data(df, market, k_type):
    """格式化市场数据"""
    formatted_data = []
    for _, row in df.iterrows():
        if k_type == "min":
            time_str = str(row.get("时间", row.get("time", "")))
        else:
            time_str = str(row.get("date", row.get("日期", ""))).split()[0]

        data_point = {
            "time": time_str,
            "open": float(row.get("开盘", row.get("open", 0))),
            "high": float(row.get("最高", row.get("high", 0))),
            "low": float(row.get("最低", row.get("low", 0))),
            "close": float(row.get("收盘", row.get("close", 0))),
            "volume": float(row.get("成交量", row.get("volume", 0))),
        }
        formatted_data.append(data_point)
    return formatted_data


@transaction.atomic
def save_market_data(data_points, market, index_info):
    """保存市场数据到数据库"""
    for point in data_points:
        MarketIndex.objects.create(
            symbol=index_info["symbol"],
            market=market,
            name=index_info["name"],
            time=datetime.strptime(
                point["time"], "%Y%m%d %H:%M" if len(point["time"]) > 10 else "%Y-%m-%d"
            ),
            open=point["open"],
            high=point["high"],
            low=point["low"],
            close=point["close"],
            volume=point["volume"],
        )


@transaction.atomic
def save_gold_data(gold_data):
    """保存黄金数据到数据库"""
    current_time = timezone.now()
    for symbol, data in gold_data.items():
        GoldIndex.objects.create(
            symbol=symbol,
            name=data["name"],
            time=current_time,
            price=data["price"],
            open=data["price"],  # 当前只能获取实时价格
            high=data["price"],
            low=data["price"],
            close=data["price"],
            change=data["change"],
            change_percent=data["change_percent"],
        )
