import logging
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view

logger = logging.getLogger(__name__)

INDEX_SYMBOLS = {
    "shangzheng": "sh000001",
    "shenzhen": "sz399001",
    "chuangye": "sz399006",
}

INDEX_NAMES = {"shangzheng": "上证指数", "shenzhen": "深证成指", "chuangye": "创业板"}


@api_view(["GET"])
def stock_index(request, index_code):
    try:
        k_type = request.GET.get("type", "min")
        start_time = request.GET.get("start_time")
        logger.info(
            f"Fetching {index_code} data with type {k_type}, start_time {start_time}"
        )

        if index_code not in INDEX_SYMBOLS:
            return JsonResponse({"error": "Invalid index code"}, status=400)

        symbol = INDEX_SYMBOLS[index_code]

        # 根据不同的K线类型获取数据
        if k_type == "min":
            try:
                # 处理指数代码格式
                clean_symbol = symbol.replace("sh", "").replace("sz", "")
                logger.info(f"Clean symbol: {clean_symbol}")

                # 获取当前时间
                now = datetime.now()
                logger.info(f"Current time: {now}")

                # 获取最近的交易日
                def get_last_trading_day():
                    try:
                        # 获取交易日历数据
                        today = now.strftime("%Y%m%d")
                        calendar_df = ak.tool_trade_date_hist_sina()
                        logger.info(
                            f"Retrieved trading calendar data: {len(calendar_df)} days"
                        )

                        # 确保日期格式正确
                        calendar_df["trade_date"] = pd.to_datetime(
                            calendar_df["trade_date"]
                        )

                        # 获取小于等于今天的最近交易日
                        today_datetime = pd.to_datetime(today)
                        last_trade_date = calendar_df[
                            calendar_df["trade_date"] <= today_datetime
                        ]["trade_date"].max()

                        logger.info(f"Found last trading day: {last_trade_date}")
                        return last_trade_date
                    except Exception as e:
                        logger.error(f"Error getting trading calendar: {str(e)}")
                        # 如果获取交易日历失败，回退到简单的周末判断
                        current_date = now
                        while current_date.weekday() >= 5:  # 5是周六，6是周日
                            current_date -= timedelta(days=1)
                        return current_date

                last_trading_day = get_last_trading_day()
                trading_date = last_trading_day.strftime("%Y%m%d")

                logger.info(f"Using trading date: {trading_date}")

                # 获取指定交易日的分时数据
                logger.info(f"Fetching minute data for trading day: {trading_date}")
                df = ak.index_zh_a_hist_min_em(
                    symbol=clean_symbol,
                    start_date=trading_date,
                    end_date=trading_date,
                    period="1",
                )

                if df.empty:
                    logger.error(f"No data available for trading day: {trading_date}")
                    raise Exception("No minute data available")

                logger.info(f"Raw DataFrame shape: {df.shape}")
                logger.info(f"Raw DataFrame columns: {df.columns.tolist()}")
                logger.info(f"Raw DataFrame head:\n{df.head()}")

                # 重命名列以匹配预期格式
                df = df.rename(
                    columns={
                        "时间": "day",
                        "开盘": "open",
                        "收盘": "close",
                        "最高": "high",
                        "最低": "low",
                        "成交量": "volume",
                    }
                )
                logger.info(f"Renamed columns: {df.columns.tolist()}")

                df = df.reset_index(drop=True)
                logger.info(f"Final DataFrame shape: {df.shape}")
                logger.info(f"Final DataFrame head:\n{df.head()}")

            except Exception as e:
                logger.error(f"Error fetching minute data: {str(e)}")
                logger.error(f"Exception type: {type(e)}")
                logger.error(f"Exception details:", exc_info=True)
                # 如果分时数据获取失败，返回最近日K数据
                df = ak.stock_zh_index_daily(symbol=symbol).tail(1)
                k_type = "daily"  # 切换到日K模式

            logger.info(f"数据列名: {df.columns.tolist()}")
            logger.info(f"数据示例:\n{df.head()}")
        elif k_type == "daily":
            # 获取日K数据，最近30天
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
            df = df.reset_index()
        elif k_type == "weekly":
            # 获取周K数据，最近30周
            df = ak.stock_zh_index_weekly(symbol=symbol).tail(30)
            df = df.reset_index()
        elif k_type == "monthly":
            # 获取月K数据，最近30月
            df = ak.stock_zh_index_monthly(symbol=symbol).tail(30)
            df = df.reset_index()
        else:
            return JsonResponse({"error": "Invalid k-line type"}, status=400)

        logger.info(f"Retrieved {len(df)} records")

        # 转换数据格式
        def format_stock_data(df):
            try:
                formatted_data = []
                for _, row in df.iterrows():
                    if k_type == "min":
                        # 对于分时数据，保留完整的日期时间
                        time_str = str(row["day"])
                        if len(time_str) == 5:  # 如果时间格式是 "HH:MM"
                            # 添加当天日期
                            date_str = trading_date
                            time_str = f"{date_str} {time_str}"
                    else:
                        # 对于其他K线类型，只保留日期
                        time_str = str(row["day"]).split()[0]

                    data_point = {
                        "time": time_str,  # 保持完整的时间信息
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]) if "volume" in row else 0,
                    }
                    formatted_data.append(data_point)

                # 记录第一个和最后一个数据点
                if formatted_data:
                    logger.info(f"First data point: {formatted_data[0]}")
                    logger.info(f"Last data point: {formatted_data[-1]}")

                return formatted_data
            except Exception as e:
                logger.error(f"Error formatting data: {str(e)}")
                raise

        data = format_stock_data(df)
        logger.info(f"Successfully formatted {len(data)} data points")
        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f"Error in stock_index view: {str(e)}", exc_info=True)
        return JsonResponse(
            {"error": str(e), "detail": "Failed to fetch stock data"}, status=500
        )


@api_view(["GET"])
def stock_quotes(request):
    try:
        quotes = {}

        def get_latest_quote(symbol, code):
            try:
                # 获取实时行情数据
                df = ak.stock_zh_index_spot_sina()  # 使用新浪财经实时行情接口

                # 修正股票代码格式，移除 'sh' 或 'sz' 前缀
                clean_symbol = symbol.replace("sh", "").replace("sz", "")

                # 找到对应指数的数据
                index_data = df[df["代码"].str.contains(clean_symbol)].iloc[0]

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

                logger.info(f"Raw index data for {code}: {index_data.to_dict()}")
                logger.info(f"Available columns: {index_data.index.tolist()}")

                return {
                    "name": INDEX_NAMES[code],
                    "current": price,
                    "change": change,
                    "changePercent": change_percent,
                }
            except Exception as e:
                logger.error(f"Error getting data for {code}: {str(e)}")
                # 如果实时数据获取失败，尝试获取日线数据
                try:
                    df = ak.index_zh_a_hist(
                        symbol=clean_symbol,
                        period="daily",
                        start_date=None,
                        end_date=None,
                    ).tail(2)
                    if len(df) >= 2:
                        today = df.iloc[-1]
                        yesterday = df.iloc[-2]
                        current = (
                            float(today["收盘"])
                            if "收盘" in today
                            else float(today["close"])
                        )
                        prev_close = (
                            float(yesterday["收盘"])
                            if "收盘" in yesterday
                            else float(yesterday["close"])
                        )
                        change = current - prev_close
                        change_percent = (
                            (change / prev_close * 100) if prev_close != 0 else 0
                        )

                        return {
                            "name": INDEX_NAMES[code],
                            "current": current,
                            "change": round(change, 2),
                            "changePercent": round(change_percent, 2),
                        }
                except Exception as backup_e:
                    logger.error(
                        f"Backup data fetch failed for {code}: {str(backup_e)}"
                    )
                return None

        # 获取每个指数的行情
        indices = [
            ("sh000001", "shangzheng"),
            ("sz399001", "shenzhen"),
            ("sz399006", "chuangye"),
        ]

        # 获取所有指数的实时行情数据
        try:
            df_all = ak.stock_zh_index_spot_sina()
            logger.info(f"Retrieved indices data columns: {df_all.columns.tolist()}")
            logger.info(f"Sample data:\n{df_all.head()}")
        except Exception as e:
            logger.error(f"Failed to fetch indices data: {str(e)}")
            df_all = None

        for symbol, code in indices:
            quote = get_latest_quote(symbol, code)
            if quote:
                quotes[code] = quote
            else:
                quotes[code] = {
                    "name": INDEX_NAMES[code],
                    "current": 0,
                    "change": 0,
                    "changePercent": 0,
                }
            logger.info(f"Processed {code} quote: {quotes[code]}")

        return JsonResponse(quotes)
    except Exception as e:
        logger.error(f"Error in stock_quotes view: {str(e)}", exc_info=True)
        return JsonResponse(
            {"error": str(e), "detail": "Failed to fetch stock quotes"}, status=500
        )
