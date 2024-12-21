from django.http import JsonResponse
from rest_framework.decorators import api_view
import akshare as ak
from datetime import datetime, timedelta
import logging
import pandas as pd

logger = logging.getLogger(__name__)

INDEX_SYMBOLS = {
    'shangzheng': 'sh000001',
    'shenzhen': 'sz399001',
    'chuangye': 'sz399006'
}

INDEX_NAMES = {
    'shangzheng': '上证指数',
    'shenzhen': '深证成指',
    'chuangye': '创业板'
}

@api_view(['GET'])
def stock_index(request, index_code):
    try:
        k_type = request.GET.get('type', 'min')
        logger.info(f"Fetching {index_code} data with type {k_type}")
        
        if index_code not in INDEX_SYMBOLS:
            return JsonResponse({'error': 'Invalid index code'}, status=400)
            
        symbol = INDEX_SYMBOLS[index_code]
        
        # 根据不同的K线类型获取数据
        if k_type == 'min':
            try:
                # 尝试使用新浪财经的分时数据接口
                df = ak.stock_zh_a_minute(symbol=symbol, period='1')
                df = df.reset_index()
            except Exception as e:
                logger.error(f"Error fetching minute data: {str(e)}")
                # 如果分时数据获取失败，返回最近日K数据
                df = ak.stock_zh_index_daily(symbol=symbol).tail(1)
                k_type = 'daily'  # 切换到日K模式
            
            logger.info(f"数据列名: {df.columns.tolist()}")
            logger.info(f"数据示例:\n{df.head()}")
        elif k_type == 'daily':
            # 获取日K数据，最近30天
            df = ak.stock_zh_index_daily(symbol=symbol).tail(30)
            df = df.reset_index()
        elif k_type == 'weekly':
            # 获取周K数据，最近30周
            df = ak.stock_zh_index_weekly(symbol=symbol).tail(30)
            df = df.reset_index()
        elif k_type == 'monthly':
            # 获取月K数据，最近30月
            df = ak.stock_zh_index_monthly(symbol=symbol).tail(30)
            df = df.reset_index()
        else:
            return JsonResponse({'error': 'Invalid k-line type'}, status=400)
            
        logger.info(f"Retrieved {len(df)} records")
        
        # 转换数据格式
        def format_stock_data(df):
            if df.empty:
                logger.warning("Empty dataframe received")
                return []
            
            formatted_data = []
            
            for _, row in df.iterrows():
                try:
                    if k_type == 'min':
                        # 分时数据直接使用 day 字段
                        time_obj = pd.to_datetime(row['day'])
                    else:
                        # 日K、周K、月K数据处理
                        time_obj = pd.to_datetime(row['date'])
                        
                    data_point = {
                        'time': time_obj.strftime('%Y-%m-%d %H:%M') if k_type == 'min' else time_obj.strftime('%Y-%m-%d'),
                        'open': float(row['open']),
                        'close': float(row['close']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'volume': float(row['volume'])
                    }
                    
                    formatted_data.append(data_point)
                except Exception as e:
                    logger.error(f"Error formatting row: {e}")
                    logger.error(f"Row data: {row.to_dict()}")
                    continue
            
            # 按时间升序排序
            formatted_data.sort(key=lambda x: x['time'])
            
            # 记录第一个和最后一个数据点
            if formatted_data:
                logger.info(f"First data point: {formatted_data[0]}")
                logger.info(f"Last data point: {formatted_data[-1]}")
            
            return formatted_data

        data = format_stock_data(df)
        logger.info(f"Successfully formatted {len(data)} data points")
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        logger.error(f"Error in stock_index view: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': str(e),
            'detail': 'Failed to fetch stock data'
        }, status=500) 

@api_view(['GET'])
def stock_quotes(request):
    try:
        quotes = {}
        
        def get_latest_quote(symbol, code):
            try:
                # 获取实时行情数据
                df = ak.stock_zh_index_spot_sina()  # 使用新浪财经实时行情接口
                
                # 修正股票代码格式，移除 'sh' 或 'sz' 前缀
                clean_symbol = symbol.replace('sh', '').replace('sz', '')
                
                # 找到对应指数的数据
                index_data = df[df['代码'].str.contains(clean_symbol)].iloc[0]
                
                # 处理不同的列名格式
                price = float(index_data.get('当前价', index_data.get('最新价', index_data.get('price', 0))))
                change = float(index_data.get('涨跌额', index_data.get('change', 0)))
                change_percent = float(index_data.get('涨跌幅', index_data.get('pct_chg', 0)))
                
                logger.info(f"Raw index data for {code}: {index_data.to_dict()}")
                logger.info(f"Available columns: {index_data.index.tolist()}")
                
                return {
                    'name': INDEX_NAMES[code],
                    'current': price,
                    'change': change,
                    'changePercent': change_percent
                }
            except Exception as e:
                logger.error(f"Error getting data for {code}: {str(e)}")
                # 如果实时数据获取失败，尝试获取日线数据
                try:
                    df = ak.index_zh_a_hist(symbol=clean_symbol, period="daily", start_date=None, end_date=None).tail(2)
                    if len(df) >= 2:
                        today = df.iloc[-1]
                        yesterday = df.iloc[-2]
                        current = float(today['收盘']) if '收盘' in today else float(today['close'])
                        prev_close = float(yesterday['收盘']) if '收盘' in yesterday else float(yesterday['close'])
                        change = current - prev_close
                        change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                        
                        return {
                            'name': INDEX_NAMES[code],
                            'current': current,
                            'change': round(change, 2),
                            'changePercent': round(change_percent, 2)
                        }
                except Exception as backup_e:
                    logger.error(f"Backup data fetch failed for {code}: {str(backup_e)}")
                return None

        # 获取每个指数的行情
        indices = [
            ('sh000001', 'shangzheng'),
            ('sz399001', 'shenzhen'),
            ('sz399006', 'chuangye')
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
                    'name': INDEX_NAMES[code],
                    'current': 0,
                    'change': 0,
                    'changePercent': 0
                }
            logger.info(f"Processed {code} quote: {quotes[code]}")

        return JsonResponse(quotes)
    except Exception as e:
        logger.error(f"Error in stock_quotes view: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': str(e),
            'detail': 'Failed to fetch stock quotes'
        }, status=500) 