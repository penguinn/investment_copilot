import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tabs, Button, Tag } from 'antd';
import {
  StarOutlined,
  StarFilled,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import styles from './index.less';

// 外汇分类
const forexCategories = [
  { key: 'major', label: '主要货币' },
  { key: 'cross', label: '交叉盘' },
  { key: 'cny', label: '人民币汇率' },
];

// 模拟外汇数据
const mockForexData: Record<string, any[]> = {
  major: [
    {
      code: 'EUR/USD',
      name: '欧元/美元',
      price: 1.0892,
      change: 0.0015,
      changePercent: 0.14,
      bid: 1.0890,
      ask: 1.0894,
      high: 1.0915,
      low: 1.0868,
    },
    {
      code: 'GBP/USD',
      name: '英镑/美元',
      price: 1.2715,
      change: -0.0028,
      changePercent: -0.22,
      bid: 1.2713,
      ask: 1.2717,
      high: 1.2758,
      low: 1.2695,
    },
    {
      code: 'USD/JPY',
      name: '美元/日元',
      price: 148.25,
      change: 0.45,
      changePercent: 0.30,
      bid: 148.23,
      ask: 148.27,
      high: 148.65,
      low: 147.82,
    },
  ],
  cross: [
    {
      code: 'EUR/GBP',
      name: '欧元/英镑',
      price: 0.8566,
      change: 0.0022,
      changePercent: 0.26,
      bid: 0.8564,
      ask: 0.8568,
      high: 0.8585,
      low: 0.8548,
    },
    {
      code: 'EUR/JPY',
      name: '欧元/日元',
      price: 161.52,
      change: 0.68,
      changePercent: 0.42,
      bid: 161.48,
      ask: 161.56,
      high: 162.15,
      low: 160.85,
    },
  ],
  cny: [
    {
      code: 'USD/CNY',
      name: '美元/人民币',
      price: 7.1850,
      change: 0.0125,
      changePercent: 0.17,
      bid: 7.1845,
      ask: 7.1855,
      high: 7.1920,
      low: 7.1725,
    },
    {
      code: 'EUR/CNY',
      name: '欧元/人民币',
      price: 7.8268,
      change: 0.0235,
      changePercent: 0.30,
      bid: 7.8258,
      ask: 7.8278,
      high: 7.8450,
      low: 7.8035,
    },
    {
      code: 'GBP/CNY',
      name: '英镑/人民币',
      price: 9.1358,
      change: -0.0142,
      changePercent: -0.16,
      bid: 9.1348,
      ask: 9.1368,
      high: 9.1650,
      low: 9.1125,
    },
    {
      code: 'JPY/CNY',
      name: '日元/人民币(100)',
      price: 4.8470,
      change: -0.0085,
      changePercent: -0.18,
      bid: 4.8465,
      ask: 4.8475,
      high: 4.8620,
      low: 4.8385,
    },
  ],
};

const Forex: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('cny');
  const [favoriteList, setFavoriteList] = useState<string[]>(['USD/CNY', 'EUR/USD']);

  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise-text';
    if (value < 0) return 'fall-text';
    return '';
  };

  const formatChange = (value: number, precision: number = 4) => {
    if (value > 0) return `+${value.toFixed(precision)}`;
    return value.toFixed(precision);
  };

  const handleToggleFavorite = (code: string) => {
    setFavoriteList((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const columns = [
    {
      title: '货币对',
      key: 'forex',
      render: (_: any, record: any) => (
        <div className={styles.forexInfo}>
          <span className={styles.forexName}>{record.code}</span>
          <span className={styles.forexDesc}>{record.name}</span>
        </div>
      ),
    },
    {
      title: '最新价',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      render: (price: number, record: any) => (
        <span className={`${styles.price} ${getChangeColor(record.change)}`}>
          {price.toFixed(4)}
        </span>
      ),
    },
    {
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      align: 'right' as const,
      render: (change: number) => (
        <span className={getChangeColor(change)}>{formatChange(change)}</span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      align: 'right' as const,
      render: (percent: number) => (
        <span className={`${styles.changePercent} ${getChangeColor(percent)}`}>
          {formatChange(percent, 2)}%
        </span>
      ),
    },
    {
      title: '买入价',
      dataIndex: 'bid',
      key: 'bid',
      align: 'right' as const,
      render: (val: number) => val.toFixed(4),
    },
    {
      title: '卖出价',
      dataIndex: 'ask',
      key: 'ask',
      align: 'right' as const,
      render: (val: number) => val.toFixed(4),
    },
    {
      title: '最高',
      dataIndex: 'high',
      key: 'high',
      align: 'right' as const,
      render: (val: number) => val.toFixed(4),
    },
    {
      title: '最低',
      dataIndex: 'low',
      key: 'low',
      align: 'right' as const,
      render: (val: number) => val.toFixed(4),
    },
    {
      title: '操作',
      key: 'action',
      align: 'center' as const,
      render: (_: any, record: any) => {
        const isFav = favoriteList.includes(record.code);
        return (
          <Button
            type="text"
            icon={isFav ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={() => handleToggleFavorite(record.code)}
          />
        );
      },
    },
  ];

  const categoryTabItems = forexCategories.map((cat) => ({
    key: cat.key,
    label: cat.label,
    children: (
      <Table
        columns={columns}
        dataSource={mockForexData[cat.key]}
        rowKey="code"
        pagination={false}
        className={styles.forexTable}
      />
    ),
  }));

  // 主要汇率展示
  const mainRates = [
    mockForexData.cny[0], // USD/CNY
    mockForexData.major[0], // EUR/USD
    mockForexData.major[2], // USD/JPY
  ];

  return (
    <div className={styles.forexPage}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>外汇市场</h1>
        <Tag color="green" icon={<SwapOutlined />}>
          24小时交易
        </Tag>
      </div>

      {/* 主要汇率卡片 */}
      <Row gutter={[16, 16]} className={styles.overviewCards}>
        {mainRates.map((item) => (
          <Col xs={24} sm={8} key={item.code}>
            <Card className={styles.rateCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>{item.code}</span>
                <span className={styles.cardDesc}>{item.name}</span>
              </div>
              <div className={styles.cardBody}>
                <Statistic
                  value={item.price}
                  precision={4}
                  valueStyle={{
                    color: item.change >= 0 ? 'var(--rise-color)' : 'var(--fall-color)',
                    fontSize: '28px',
                    fontWeight: 700,
                    fontFamily: "'SF Mono', 'Monaco', 'Consolas', monospace",
                  }}
                />
                <div className={styles.changeInfo}>
                  <span className={getChangeColor(item.change)}>
                    {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    {formatChange(item.change)}
                  </span>
                  <span className={`${styles.changePercent} ${getChangeColor(item.changePercent)}`}>
                    {formatChange(item.changePercent, 2)}%
                  </span>
                </div>
                <div className={styles.bidAsk}>
                  <span>买: {item.bid.toFixed(4)}</span>
                  <span>卖: {item.ask.toFixed(4)}</span>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 汇率列表 */}
      <Card className={styles.listCard}>
        <Tabs
          activeKey={activeCategory}
          onChange={setActiveCategory}
          items={categoryTabItems}
        />
      </Card>
    </div>
  );
};

export default Forex;
