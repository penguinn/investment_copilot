import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spin, Button, Tooltip } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  RobotOutlined,
  StockOutlined,
  FundOutlined,
  GoldOutlined,
  LineChartOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { marketApi, goldApi, fundApi, futuresApi } from '@/services/api';
import NewsCard from '@/components/NewsCard';
import styles from './index.less';

// 刷新间隔（5分钟）
const REFRESH_INTERVAL = 5 * 60 * 1000;

// 股票指数配置
const STOCK_INDICES = {
  CN: [
    { code: 'SSE', name: '上证指数' },
    { code: 'SZSE', name: '深证成指' },
    { code: 'ChiNext', name: '创业板指' },
  ],
  HK: [
    { code: 'HSI', name: '恒生指数' },
    { code: 'HSCEI', name: '恒生国企' },
    { code: 'HSTECH', name: '恒生科技' },
  ],
  US: [
    { code: 'DJI', name: '道琼斯' },
    { code: 'IXIC', name: '纳斯达克' },
    { code: 'SPX', name: '标普500' },
  ],
};

// 默认数据
const DEFAULT_DATA = {
  stock: {
    CN: [
      { code: 'SSE', name: '上证指数', price: 3350.44, change: 18.32, changePercent: 0.55 },
      { code: 'SZSE', name: '深证成指', price: 10856.28, change: 58.45, changePercent: 0.54 },
      { code: 'ChiNext', name: '创业板指', price: 2158.62, change: 22.86, changePercent: 1.07 },
    ],
    HK: [
      { code: 'HSI', name: '恒生指数', price: 26844.96, change: -78.66, changePercent: -0.29 },
      { code: 'HSCEI', name: '恒生国企', price: 9220.81, change: -46.05, changePercent: -0.50 },
      { code: 'HSTECH', name: '恒生科技', price: 5822.18, change: -6.17, changePercent: -0.11 },
    ],
    US: [
      { code: 'DJI', name: '道琼斯', price: 49359.33, change: 186.74, changePercent: 0.38 },
      { code: 'IXIC', name: '纳斯达克', price: 23515.39, change: 78.52, changePercent: 0.33 },
      { code: 'SPX', name: '标普500', price: 6940.01, change: 22.68, changePercent: 0.33 },
    ],
  },
  gold: [
    { code: 'XAU', name: '现货黄金', price: 2045.60, change: 5.60, changePercent: 0.27, unit: '美元/盎司' },
    { code: 'XAG', name: '现货白银', price: 23.15, change: 0.15, changePercent: 0.65, unit: '美元/盎司' },
  ],
  fund: [
    { code: 'FUND_股票型', name: '股票型', fundType: '股票型', avgChange: 0.85, total: 1520, rise: 980, fall: 540 },
    { code: 'FUND_混合型', name: '混合型', fundType: '混合型', avgChange: -0.42, total: 3250, rise: 1200, fall: 2050 },
    { code: 'FUND_债券型', name: '债券型', fundType: '债券型', avgChange: 0.12, total: 2180, rise: 1350, fall: 830 },
    { code: 'FUND_指数型', name: '指数型', fundType: '指数型', avgChange: 0.68, total: 1680, rise: 1100, fall: 580 },
  ],
  futures: [
    { code: 'IF2401', name: '沪深300期货', price: 3658.4, change: 25.6, changePercent: 0.70 },
    { code: 'SC2402', name: '原油期货', price: 568.5, change: 8.6, changePercent: 1.54 },
    { code: 'AU2402', name: '黄金期货', price: 486.52, change: 3.28, changePercent: 0.68 },
  ],
};

interface IndexData {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface GoldData {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  unit: string;
}

interface FundData {
  code: string;
  name: string;
  fundType: string;
  avgChange: number;
  total: number;
  rise: number;
  fall: number;
}

interface FuturesData {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

const Dashboard: React.FC = () => {
  const [activeStockMarket, setActiveStockMarket] = useState('CN');
  
  // 各模块独立的 loading 状态
  const [stockLoading, setStockLoading] = useState(false);
  const [goldLoading, setGoldLoading] = useState(false);
  const [fundLoading, setFundLoading] = useState(false);
  const [futuresLoading, setFuturesLoading] = useState(false);
  
  // 数据状态（初始化为默认数据）
  const [stockData, setStockData] = useState<Record<string, IndexData[]>>(DEFAULT_DATA.stock);
  const [fundData, setFundData] = useState<FundData[]>(DEFAULT_DATA.fund);
  const [goldData, setGoldData] = useState<GoldData[]>(DEFAULT_DATA.gold);
  const [futuresData, setFuturesData] = useState<FuturesData[]>(DEFAULT_DATA.futures);

  // 获取股票指数数据
  const fetchStockData = async () => {
    if (stockLoading) return;
    setStockLoading(true);
    const result: Record<string, IndexData[]> = { ...stockData };
    
    // 并行获取各市场数据
    const promises = (['CN', 'HK', 'US'] as const).map(async (market) => {
      const codes = STOCK_INDICES[market].map(item => item.code);
      try {
        const dataList = await marketApi.getIndices(market, codes);
        if (dataList && dataList.length > 0) {
          result[market] = dataList.map((item: any) => ({
            code: item.symbol || item.code,
            name: item.name,
            price: item.close || item.price || 0,
            change: item.change || 0,
            changePercent: item.change_percent || item.changePercent || 0,
          }));
      }
    } catch (error) {
        console.error(`获取${market}市场数据失败:`, error);
    }
    });
    
    await Promise.allSettled(promises);
    setStockData(result);
    setStockLoading(false);
  };

  // 获取黄金数据
  const fetchGoldData = async () => {
    if (goldLoading) return;
    setGoldLoading(true);
    try {
      const data = await goldApi.getRealtime();
      if (data && data.length > 0) {
        const formattedData = data.slice(0, 4).map((item: any) => ({
          code: item.code || item.symbol,
          name: item.name,
          price: parseFloat(item.price) || 0,
          change: parseFloat(item.change) || 0,
          changePercent: parseFloat(item.change_percent || item.changePercent) || 0,
          unit: item.unit || '美元/盎司',
        }));
        setGoldData(formattedData);
      }
    } catch (error) {
      console.error('获取黄金数据失败:', error);
    }
    setGoldLoading(false);
  };

  // 获取基金数据
  const fetchFundData = async () => {
    if (fundLoading) return;
    setFundLoading(true);
    try {
      const data = await fundApi.getSummary();
      if (data && data.length > 0) {
        const formattedData = data.map((item: any) => ({
          code: item.code,
          name: item.name,
          fundType: item.fund_type || item.fundType,
          avgChange: parseFloat(item.avg_change || item.avgChange) || 0,
          total: item.total || 0,
          rise: item.rise || 0,
          fall: item.fall || 0,
        }));
        setFundData(formattedData);
      }
    } catch (error) {
      console.error('获取基金数据失败:', error);
    }
    setFundLoading(false);
  };

  // 获取期货数据
  const fetchFuturesData = async () => {
    if (futuresLoading) return;
    setFuturesLoading(true);
    try {
      const data = await futuresApi.getRealtime();
      if (data && data.length > 0) {
        const formattedData = data.slice(0, 3).map((item: any) => ({
          code: item.code || item.symbol,
          name: item.name,
          price: parseFloat(item.price) || 0,
          change: parseFloat(item.change) || 0,
          changePercent: parseFloat(item.change_percent || item.changePercent) || 0,
        }));
        setFuturesData(formattedData);
      }
    } catch (error) {
      console.error('获取期货数据失败:', error);
    }
    setFuturesLoading(false);
  };

  // 初始化数据 - 各模块独立加载，不互相阻塞
  useEffect(() => {
    // 立即开始加载各模块数据
    fetchStockData();
    fetchGoldData();
    fetchFundData();
    fetchFuturesData();

    // 每 5 分钟刷新一次数据
    const timer = setInterval(() => {
      fetchStockData();
      fetchGoldData();
      fetchFundData();
      fetchFuturesData();
    }, REFRESH_INTERVAL);
    
    return () => clearInterval(timer);
  }, []);

  // 股票大盘跑马灯 - 每30秒自动切换市场
  useEffect(() => {
    const markets = ['CN', 'HK', 'US'];
    const carouselTimer = setInterval(() => {
      setActiveStockMarket((current) => {
        const currentIndex = markets.indexOf(current);
        const nextIndex = (currentIndex + 1) % markets.length;
        return markets[nextIndex];
      });
    }, 30000); // 30秒切换一次
    
    return () => clearInterval(carouselTimer);
  }, []);

  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise';
    if (value < 0) return 'fall';
    return 'neutral';
  };

  // 格式化价格（两位小数，带千分位）
  const formatPrice = (value: number) => {
    return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  // 格式化涨跌（两位小数，带正负号）
  const formatChange = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}`;
    return value.toFixed(2);
  };

  const stockMarketTabs = [
    { key: 'CN', label: 'A股' },
    { key: 'HK', label: '港股' },
    { key: 'US', label: '美股' },
  ];

  const currentStockData = stockData[activeStockMarket] || [];

  // 刷新按钮组件
  const RefreshButton: React.FC<{ loading: boolean; onClick: () => void }> = ({ loading, onClick }) => (
    <Tooltip title="刷新数据">
      <Button
        type="text"
        size="small"
        icon={<ReloadOutlined spin={loading} />}
        onClick={onClick}
        disabled={loading}
        className={styles.refreshBtn}
      />
    </Tooltip>
  );

  return (
    <div className={styles.dashboard}>
      {/* AI 推荐窗口 */}
      <Card className={styles.aiCard}>
        <div className={styles.aiHeader}>
          <div className={styles.aiTitle}>
            <RobotOutlined className={styles.aiIcon} />
            <span>AI 投资助手</span>
          </div>
          <span className={styles.aiBeta}>Beta</span>
        </div>
        <div className={styles.aiContent}>
          <div className={styles.aiMessage}>
            <p>👋 你好！我是你的 AI 投资助手。</p>
            <p>我可以帮你分析市场走势、推荐投资组合、解读财经新闻。</p>
            <p className={styles.aiHint}>功能开发中，敬请期待...</p>
          </div>
        </div>
        <div className={styles.aiInputArea}>
          <input
            type="text"
            placeholder="输入你的投资问题..."
            className={styles.aiInput}
            disabled
          />
          <button className={styles.aiSendBtn} disabled>
            发送
          </button>
        </div>
      </Card>

      {/* 股票大盘 */}
      <Spin spinning={stockLoading}>
        <Card className={styles.marketCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>
              <StockOutlined />
              <span>股票大盘</span>
              <RefreshButton loading={stockLoading} onClick={fetchStockData} />
            </div>
            <div className={styles.marketTabs}>
              {stockMarketTabs.map((tab) => (
                <span
                  key={tab.key}
                  className={`${styles.marketTab} ${activeStockMarket === tab.key ? styles.active : ''}`}
                  onClick={() => setActiveStockMarket(tab.key)}
                >
                  {tab.label}
                </span>
              ))}
            </div>
          </div>
          <Row gutter={[16, 16]}>
            {currentStockData.map((item) => (
              <Col xs={24} sm={12} md={8} key={item.code}>
                <div className={`${styles.indexItem} ${styles[getChangeColor(item.change)]}`}>
                  <div className={styles.indexName}>{item.name}</div>
                  <div className={styles.indexPrice}>{formatPrice(item.price)}</div>
                  <div className={styles.indexChange}>
                    {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    <span>{formatChange(item.change)}</span>
                    <span className={styles.percent}>{formatChange(item.changePercent)}%</span>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      </Spin>

      <Row gutter={[16, 16]}>
        {/* 基金大盘 */}
        <Col xs={24} lg={12}>
          <Spin spinning={fundLoading}>
            <Card className={styles.marketCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <FundOutlined />
                  <span>基金大盘</span>
                  <RefreshButton loading={fundLoading} onClick={fetchFundData} />
                </div>
              </div>
              <div className={styles.fundList}>
                {fundData.map((item) => (
                  <div key={item.code} className={styles.fundItem}>
                    <span className={styles.fundName}>{item.name}</span>
                    <span className={`${styles.fundAvgChange} ${styles[getChangeColor(item.avgChange)]}`}>
                      {item.avgChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                      {formatChange(item.avgChange)}%
                    </span>
                    <span className={styles.fundStats}>
                      <span className={styles.rise}>↑{item.rise}</span>
                      <span className={styles.fall}>↓{item.fall}</span>
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </Spin>
        </Col>

        {/* 黄金大盘 */}
        <Col xs={24} lg={12}>
          <Spin spinning={goldLoading}>
            <Card className={`${styles.marketCard} ${styles.goldCard}`}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <GoldOutlined />
                  <span>黄金大盘</span>
                  <RefreshButton loading={goldLoading} onClick={fetchGoldData} />
                </div>
              </div>
              <Row gutter={[16, 16]}>
                {goldData.map((item) => (
                  <Col span={12} key={item.code}>
                    <div className={styles.goldItem}>
                      <div className={styles.goldName}>{item.name}</div>
                      <div className={`${styles.goldPrice} ${styles[getChangeColor(item.change)]}`}>
                        {item.price.toFixed(2)}
                        <span className={styles.goldUnit}>{item.unit}</span>
                      </div>
                      <div className={`${styles.goldChange} ${styles[getChangeColor(item.change)]}`}>
                        {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                        {formatChange(item.change)} ({formatChange(item.changePercent)}%)
                      </div>
                    </div>
        </Col>
                ))}
              </Row>
            </Card>
          </Spin>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 期货大盘 */}
        <Col xs={24} lg={12}>
          <Spin spinning={futuresLoading}>
            <Card className={styles.marketCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <LineChartOutlined />
                  <span>期货大盘</span>
                  <RefreshButton loading={futuresLoading} onClick={fetchFuturesData} />
                </div>
              </div>
              <Row gutter={[16, 16]}>
                {futuresData.map((item) => (
                  <Col xs={24} key={item.code}>
                    <div className={`${styles.futuresItem} ${styles[getChangeColor(item.change)]}`}>
                      <div className={styles.futuresHeader}>
                        <span className={styles.futuresName}>{item.name}</span>
                        <span className={styles.futuresCode}>{item.code}</span>
                      </div>
                      <div className={styles.futuresPrice}>{item.price.toFixed(2)}</div>
                      <div className={styles.futuresChange}>
                        {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                        <span>{formatChange(item.change)}</span>
                        <span className={styles.percent}>{formatChange(item.changePercent)}%</span>
                      </div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card>
          </Spin>
        </Col>

        {/* 资讯快报 */}
        <Col xs={24} lg={12}>
          <NewsCard height={300} />
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard; 
