import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tabs, Empty, Button } from 'antd';
import {
  StarOutlined,
  StarFilled,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import styles from './index.less';

// 期货品种分类
const futuresCategories = [
  { key: 'index', label: '股指期货' },
  { key: 'commodity', label: '商品期货' },
  { key: 'bond', label: '国债期货' },
];

// 模拟期货数据
const mockFuturesData: Record<string, any[]> = {
  index: [
    {
      code: 'IF2401',
      name: '沪深300股指期货',
      price: 3658.4,
      change: 25.6,
      changePercent: 0.70,
      open: 3640.2,
      high: 3672.8,
      low: 3635.0,
      volume: '12.5万手',
      position: '18.2万手',
    },
    {
      code: 'IC2401',
      name: '中证500股指期货',
      price: 5428.6,
      change: -32.4,
      changePercent: -0.59,
      open: 5465.0,
      high: 5478.2,
      low: 5412.4,
      volume: '8.3万手',
      position: '12.6万手',
    },
    {
      code: 'IH2401',
      name: '上证50股指期货',
      price: 2485.2,
      change: 18.8,
      changePercent: 0.76,
      open: 2470.4,
      high: 2498.6,
      low: 2468.0,
      volume: '6.8万手',
      position: '9.4万手',
    },
  ],
  commodity: [
    {
      code: 'AU2402',
      name: '黄金期货',
      price: 486.52,
      change: 3.28,
      changePercent: 0.68,
      open: 484.00,
      high: 488.20,
      low: 483.50,
      volume: '25.6万手',
      position: '32.4万手',
    },
    {
      code: 'CU2402',
      name: '铜期货',
      price: 68450,
      change: -280,
      changePercent: -0.41,
      open: 68750,
      high: 68920,
      low: 68200,
      volume: '18.2万手',
      position: '24.8万手',
    },
    {
      code: 'SC2402',
      name: '原油期货',
      price: 568.5,
      change: 8.6,
      changePercent: 1.54,
      open: 562.0,
      high: 572.8,
      low: 560.4,
      volume: '32.4万手',
      position: '45.2万手',
    },
  ],
  bond: [
    {
      code: 'T2403',
      name: '10年期国债期货',
      price: 103.825,
      change: 0.125,
      changePercent: 0.12,
      open: 103.720,
      high: 103.880,
      low: 103.680,
      volume: '8.5万手',
      position: '12.3万手',
    },
    {
      code: 'TF2403',
      name: '5年期国债期货',
      price: 102.465,
      change: 0.085,
      changePercent: 0.08,
      open: 102.400,
      high: 102.520,
      low: 102.380,
      volume: '5.2万手',
      position: '8.6万手',
    },
  ],
};

const Futures: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('index');
  const [favoriteList, setFavoriteList] = useState<string[]>(['IF2401', 'AU2402']);

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
    setFavoriteList((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const columns = [
    {
      title: '合约',
      key: 'futures',
      render: (_: any, record: any) => (
        <div className={styles.futuresInfo}>
          <span className={styles.futuresName}>{record.name}</span>
          <span className={styles.futuresCode}>{record.code}</span>
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
      title: '开盘',
      dataIndex: 'open',
      key: 'open',
      align: 'right' as const,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '最高',
      dataIndex: 'high',
      key: 'high',
      align: 'right' as const,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '最低',
      dataIndex: 'low',
      key: 'low',
      align: 'right' as const,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      align: 'right' as const,
    },
    {
      title: '持仓量',
      dataIndex: 'position',
      key: 'position',
      align: 'right' as const,
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

  // 获取所有收藏的期货
  const getFavoriteFutures = () => {
    const allFutures = Object.values(mockFuturesData).flat();
    return allFutures.filter((f) => favoriteList.includes(f.code));
  };

  const categoryTabItems = futuresCategories.map((cat) => ({
    key: cat.key,
    label: cat.label,
    children: (
      <Table
        columns={columns}
        dataSource={mockFuturesData[cat.key]}
        rowKey="code"
        pagination={false}
        className={styles.futuresTable}
      />
    ),
  }));

  return (
    <div className={styles.futuresPage}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>期货市场</h1>
      </div>

      {/* 热门期货概览 */}
      <Row gutter={[16, 16]} className={styles.overviewCards}>
        {[
          mockFuturesData.index[0],
          mockFuturesData.commodity[2],
          mockFuturesData.bond[0],
        ].map((item) => (
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

      {/* 自选期货 */}
      {favoriteList.length > 0 && (
        <Card className={styles.favoriteCard}>
          <div className={styles.sectionTitle}>
            <StarFilled style={{ color: '#faad14' }} />
            <span>自选期货</span>
            <span className={styles.count}>({favoriteList.length})</span>
          </div>
          <Table
            columns={columns}
            dataSource={getFavoriteFutures()}
            rowKey="code"
            pagination={false}
            className={styles.futuresTable}
          />
        </Card>
      )}

      {/* 期货分类列表 */}
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

export default Futures;
