import React, { useEffect, useState, useRef } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Stock } from '@ant-design/charts';
import { Card, Row, Col, Radio, Statistic, Spin, message, Space, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const { Text } = Typography;

interface StockData {
  time: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

interface StockConfig {
  xField: string;
  yField: [string, string, string, string];
  data: StockData[];
}

interface IndexQuote {
  name: string;
  current: number;
  change: number;
  changePercent: number;
}

type KLineType = 'min' | 'daily' | 'weekly' | 'monthly';

const DEFAULT_QUOTES: Record<string, IndexQuote> = {
  shangzheng: { name: '上证指数', current: 0, change: 0, changePercent: 0 },
  shenzhen: { name: '深证成指', current: 0, change: 0, changePercent: 0 },
  chuangye: { name: '创业板', current: 0, change: 0, changePercent: 0 },
};

const IndexPage: React.FC = () => {
  const [activeIndex, setActiveIndex] = useState<string | null>(null);
  const [kLineType, setKLineType] = useState<KLineType>('min');
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(false);
  const [quotesLoading, setQuotesLoading] = useState(true);
  const [quotes, setQuotes] = useState<Record<string, IndexQuote>>(DEFAULT_QUOTES);

  // 获取实时行情
  const fetchQuotes = async () => {
    try {
      setQuotesLoading(true);
      const response = await fetch('http://localhost:8080/api/stock/quotes');
      if (!response.ok) {
        throw new Error('Failed to fetch quotes');
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setQuotes(data);
    } catch (error) {
      console.error('Error fetching quotes:', error);
      message.error('获取行情数据失败');
    } finally {
      setQuotesLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotes();
    // 每分钟更新一次行情
    const timer = setInterval(fetchQuotes, 60000);
    return () => clearInterval(timer);
  }, []);

  const fetchStockData = async (index: string, type: KLineType) => {
    setLoading(true);
    try {
      const now = Math.floor(Date.now() / 1000);
      const hours24 = 24 * 60 * 60; // 24小时的秒数
      const url = type === 'min' 
        ? `http://localhost:8080/api/stock/${index}?type=${type}&start_time=${now - hours24}`
        : `http://localhost:8080/api/stock/${index}?type=${type}`;
        
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch stock data');
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setStockData(data || []);
    } catch (error) {
      console.error('Error fetching stock data:', error);
      message.error('获取K线数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (key: string) => {
    setActiveIndex(key);
    if (key) {
      fetchStockData(key, kLineType);
    }
  };

  const handleKLineTypeChange = (e: any) => {
    const newType = e.target.value as KLineType;
    setKLineType(newType);
    if (activeIndex) {
      fetchStockData(activeIndex, newType);
    }
  };

  const config: StockConfig = {
    xField: 'time',
    yField: ['open', 'close', 'high', 'low'] as [string, string, string, string],
    data: stockData
  };

  const renderQuoteCard = (indexKey: string) => {
    const quote = quotes[indexKey];
    const isPositive = quote.change >= 0;
    const color = isPositive ? '#cf1322': '#3f8600';
    

    return (
      <Col span={8} key={indexKey}>
        <Card 
          hoverable 
          onClick={() => handleTabChange(indexKey)}
          loading={quotesLoading}
        >
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Statistic
              title={quote.name}
              value={quote.current}
              precision={2}
              valueStyle={{ color, marginBottom: 0 }}
              prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
            <Space>
              <Text style={{ color }}>
                {isPositive ? '+' : ''}{quote.change.toFixed(2)}
              </Text>
              <Text style={{ color }}>
                {isPositive ? '+' : ''}{quote.changePercent.toFixed(2)}%
              </Text>
            </Space>
          </Space>
        </Card>
      </Col>
    );
  };

  const StockChart = ({ data, type }: { data: StockData[]; type: KLineType }) => {
    const chartRef = useRef<HTMLDivElement>(null);
    const chartInstance = useRef<echarts.ECharts | null>(null);

    useEffect(() => {
      if (!chartRef.current) return;

      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current);
      }

      const option: echarts.EChartsOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: (params: any) => {
            // K线图数据
            const candleStick = params.find((param: any) => param.seriesType === 'candlestick');
            // 成交量数据
            const volume = params.find((param: any) => param.seriesName === '成交量');
            
            if (!candleStick) return '';
            
            const time = type === 'min' ? 
              candleStick.axisValue.slice(-5) : 
              candleStick.axisValue;
              
            return `
              时间：${time}<br/>
              开盘：${candleStick.data[0]}<br/>
              收盘：${candleStick.data[1]}<br/>
              最低：${candleStick.data[2]}<br/>
              最高：${candleStick.data[3]}<br/>
              成交量：${volume ? volume.data : '-'}
            `;
          }
        },
        grid: [{
          left: '3%',
          right: '3%',
          height: '60%'
        }, {
          left: '3%',
          right: '3%',
          top: '75%',
          height: '20%'
        }],
        xAxis: [{
          type: 'category',
          data: data.map(item => type === 'min' ? item.time.slice(-5) : item.time),
          axisLabel: {
            formatter: (value: string) => {
              if (type === 'min') {
                return value.slice(-5);
              }
              return value;
            }
          },
          gridIndex: 0
        }, {
          type: 'category',
          gridIndex: 1,
          data: data.map(item => type === 'min' ? item.time.slice(-5) : item.time),
          axisLabel: {show: false}
        }],
        yAxis: [{
          scale: true,
          splitLine: {
            show: true
          },
          gridIndex: 0
        }, {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: {show: false}
        }],
        series: [
          {
            type: 'candlestick',
            data: data.map(item => ([
              item.open,
              item.close,
              item.low,
              item.high
            ])),
            itemStyle: {
              color: '#ef232a',
              color0: '#14b143',
              borderColor: '#ef232a',
              borderColor0: '#14b143'
            },
            xAxisIndex: 0,
            yAxisIndex: 0
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: data.map(item => item.volume)
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 0,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '0%',
            start: 0,
            end: 100
          }
        ]
      };

      chartInstance.current.setOption(option);

      // 添加窗口大小变化的监听
      const handleResize = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }, [data, type]);

    return <div ref={chartRef} style={{ width: '100%', height: '500px' }} />;
  };

  return (
    <PageContainer>
      <Row gutter={[16, 16]}>
        {Object.keys(DEFAULT_QUOTES).map(renderQuoteCard)}
      </Row>
      
      {activeIndex && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 16 }}>
            <Radio.Group 
              value={kLineType}
              onChange={handleKLineTypeChange}
            >
              <Radio.Button value="min">分时</Radio.Button>
              <Radio.Button value="daily">日K</Radio.Button>
              <Radio.Button value="weekly">周K</Radio.Button>
              <Radio.Button value="monthly">月K</Radio.Button>
            </Radio.Group>
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Spin size="large" />
            </div>
          ) : (
            <StockChart data={stockData} type={kLineType} />
          )}
        </Card>
      )}
    </PageContainer>
  );
};

export default IndexPage; 