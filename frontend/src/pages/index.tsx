import React, { useEffect, useState } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Stock } from '@ant-design/charts';
import { Card, Row, Col, Radio, Statistic, Spin, message, Space, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

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
  chuangye: { name: '创业板指', current: 0, change: 0, changePercent: 0 },
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
      const response = await fetch(`http://localhost:8080/api/stock/${index}?type=${type}`);
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
            <Stock {...config} />
          )}
        </Card>
      )}
    </PageContainer>
  );
};

export default IndexPage; 