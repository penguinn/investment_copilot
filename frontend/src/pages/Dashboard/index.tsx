import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, Typography } from 'antd';
import { KLineChart } from '@/components/KLineChart';
import { IndexCard } from '@/components/IndexCard';
import { GoldCard } from '@/components/GoldCard';
import styles from './index.less';

const { Title } = Typography;
const { TabPane } = Tabs;

const Dashboard: React.FC = () => {
  const [activeMarket, setActiveMarket] = useState('CN');
  const [activeIndex, setActiveIndex] = useState('SSE');
  const [marketData, setMarketData] = useState<any>(null);
  const [goldData, setGoldData] = useState<any>(null);

  // 获取市场指数数据
  const fetchMarketData = async () => {
    try {
      const response = await fetch(
        `/api/market/${activeMarket}/${activeIndex}?chart_type=kline&period=15min`
      );
      const data = await response.json();
      if (data.code === 0) {
        setMarketData(data.data);
      } else {
        console.error('Failed to fetch market data:', data.message);
      }
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
  };

  // 获取黄金数据
  const fetchGoldData = async () => {
    try {
      const response = await fetch('/api/gold');
      const data = await response.json();
      if (data.code === 0) {
        setGoldData(data.data);
      } else {
        console.error('Failed to fetch gold data:', data.message);
      }
    } catch (error) {
      console.error('Failed to fetch gold data:', error);
    }
  };

  useEffect(() => {
    fetchMarketData();
    fetchGoldData();
    // 每分钟更新一次数据
    const timer = setInterval(() => {
      fetchMarketData();
      fetchGoldData();
    }, 60000);
    return () => clearInterval(timer);
  }, [activeMarket, activeIndex]);

  return (
    <div className={styles.dashboard}>
      <Title level={4}>市场行情</Title>
      <Row gutter={[16, 16]}>
        {/* 市场指数卡片 */}
        <Col span={8}>
          <IndexCard
            market="CN"
            data={marketData}
            title="A股市场"
            onSelect={(market, index) => {
              setActiveMarket(market);
              setActiveIndex(index);
            }}
          />
        </Col>
        <Col span={8}>
          <IndexCard
            market="HK"
            data={marketData}
            title="港股市场"
            onSelect={(market, index) => {
              setActiveMarket(market);
              setActiveIndex(index);
            }}
          />
        </Col>
        <Col span={8}>
          <IndexCard
            market="US"
            data={marketData}
            title="美股市场"
            onSelect={(market, index) => {
              setActiveMarket(market);
              setActiveIndex(index);
            }}
          />
        </Col>
      </Row>

      {/* 黄金市场卡片 */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col span={24}>
          <GoldCard data={goldData} />
        </Col>
      </Row>

      {/* K线图 */}
      <Row style={{ marginTop: '16px' }}>
        <Col span={24}>
          <Card>
            <Tabs defaultActiveKey="kline">
              <TabPane tab="分时K线" key="kline">
                <KLineChart data={marketData?.items || []} />
              </TabPane>
              <TabPane tab="走势图" key="trend">
                {/* 可以添加走势图组件 */}
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard; 