import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Input, Button, Space, Empty, Tabs } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  StarOutlined,
  StarFilled,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import styles from './index.less';

const { Search } = Input;

// 模拟黄金市场数据
const mockGoldMarket = [
  {
    code: 'AU9999',
    name: '黄金9999',
    price: 485.32,
    change: 2.15,
    changePercent: 0.45,
    high: 487.50,
    low: 482.10,
    volume: '12,345kg',
  },
  {
    code: 'AU9995',
    name: '黄金9995',
    price: 484.88,
    change: 1.98,
    changePercent: 0.41,
    high: 486.80,
    low: 481.90,
    volume: '8,234kg',
  },
  {
    code: 'XAU',
    name: '伦敦金',
    price: 2045.60,
    change: -5.30,
    changePercent: -0.26,
    high: 2052.80,
    low: 2038.50,
    volume: '-',
  },
];

// 模拟自选黄金
const mockFavoriteGold = [
  {
    code: 'AU9999',
    name: '黄金9999',
    exchange: '上海黄金交易所',
    price: 485.32,
    change: 2.15,
    changePercent: 0.45,
    isFavorite: true,
  },
];

const Gold: React.FC = () => {
  const [goldMarket, setGoldMarket] = useState(mockGoldMarket);
  const [favoriteGold, setFavoriteGold] = useState(mockFavoriteGold);
  const [activeTab, setActiveTab] = useState('market');

  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise-text';
    if (value < 0) return 'fall-text';
    return '';
  };

  const formatChange = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}`;
    return value.toFixed(2);
  };

  const handleToggleFavorite = (code: string) => {
    const goldItem = goldMarket.find((g) => g.code === code);
    if (!goldItem) return;

    const exists = favoriteGold.find((g) => g.code === code);
    if (exists) {
      setFavoriteGold((prev) => prev.filter((g) => g.code !== code));
    } else {
      setFavoriteGold((prev) => [
        ...prev,
        {
          code: goldItem.code,
          name: goldItem.name,
          exchange: code.startsWith('AU') ? '上海黄金交易所' : '伦敦金银市场',
          price: goldItem.price,
          change: goldItem.change,
          changePercent: goldItem.changePercent,
          isFavorite: true,
        },
      ]);
    }
  };

  const marketColumns = [
    {
      title: '品种',
      key: 'gold',
      render: (_: any, record: any) => (
        <div className={styles.goldInfo}>
          <span className={styles.goldName}>{record.name}</span>
          <span className={styles.goldCode}>{record.code}</span>
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
          {price.toFixed(2)}
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
          {formatChange(percent)}%
        </span>
      ),
    },
    {
      title: '最高',
      dataIndex: 'high',
      key: 'high',
      align: 'right' as const,
      render: (high: number) => high.toFixed(2),
    },
    {
      title: '最低',
      dataIndex: 'low',
      key: 'low',
      align: 'right' as const,
      render: (low: number) => low.toFixed(2),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      align: 'right' as const,
    },
    {
      title: '操作',
      key: 'action',
      align: 'center' as const,
      render: (_: any, record: any) => {
        const isFav = favoriteGold.some((g) => g.code === record.code);
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

  const tabItems = [
    {
      key: 'market',
      label: '黄金市场',
      children: (
        <Table
          columns={marketColumns}
          dataSource={goldMarket}
          rowKey="code"
          pagination={false}
          className={styles.goldTable}
        />
      ),
    },
    {
      key: 'favorite',
      label: `自选 (${favoriteGold.length})`,
      children: favoriteGold.length > 0 ? (
        <Table
          columns={marketColumns}
          dataSource={favoriteGold}
          rowKey="code"
          pagination={false}
          className={styles.goldTable}
        />
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无自选黄金"
        />
      ),
    },
  ];

  return (
    <div className={styles.goldPage}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>黄金市场</h1>
      </div>

      {/* 黄金实时行情卡片 */}
      <Row gutter={[16, 16]} className={styles.overviewCards}>
        {goldMarket.slice(0, 3).map((item) => (
          <Col xs={24} sm={8} key={item.code}>
            <Card className={styles.priceCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>{item.name}</span>
                <span className={styles.cardCode}>{item.code}</span>
              </div>
              <div className={styles.cardBody}>
                <Statistic
                  value={item.price}
                  precision={2}
                  valueStyle={{
                    color: item.change >= 0 ? 'var(--rise-color)' : 'var(--fall-color)',
                    fontSize: '28px',
                    fontWeight: 700,
                    fontFamily: "'SF Mono', 'Monaco', 'Consolas', monospace",
                  }}
                  suffix={item.code.startsWith('AU') ? '元/克' : '美元/盎司'}
                />
                <div className={styles.changeInfo}>
                  <span className={getChangeColor(item.change)}>
                    {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    {formatChange(item.change)}
                  </span>
                  <span className={`${styles.changePercent} ${getChangeColor(item.changePercent)}`}>
                    {formatChange(item.changePercent)}%
                  </span>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 黄金列表 */}
      <Card className={styles.listCard}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
};

export default Gold;
