import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tabs, Button, Tag } from 'antd';
import {
  StarOutlined,
  StarFilled,
  ArrowUpOutlined,
  ArrowDownOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import styles from './index.less';

// 债券分类
const bondCategories = [
  { key: 'treasury', label: '国债' },
  { key: 'corporate', label: '企业债' },
  { key: 'convertible', label: '可转债' },
];

// 模拟国债收益率数据
const treasuryYields = [
  { term: '1年期', yield: 2.15, change: 0.02, prev: 2.13 },
  { term: '2年期', yield: 2.28, change: -0.01, prev: 2.29 },
  { term: '5年期', yield: 2.45, change: 0.03, prev: 2.42 },
  { term: '10年期', yield: 2.68, change: 0.01, prev: 2.67 },
  { term: '30年期', yield: 2.95, change: -0.02, prev: 2.97 },
];

// 模拟债券数据
const mockBondData: Record<string, any[]> = {
  treasury: [
    {
      code: '019701',
      name: '24国债01',
      price: 100.25,
      change: 0.12,
      changePercent: 0.12,
      yield: 2.68,
      maturity: '2034-01-15',
      rating: 'AAA',
    },
    {
      code: '019702',
      name: '24国债02',
      price: 99.85,
      change: -0.08,
      changePercent: -0.08,
      yield: 2.72,
      maturity: '2034-03-20',
      rating: 'AAA',
    },
  ],
  corporate: [
    {
      code: '143521',
      name: '华能国际债',
      price: 101.50,
      change: 0.25,
      changePercent: 0.25,
      yield: 3.45,
      maturity: '2028-06-15',
      rating: 'AAA',
    },
    {
      code: '143522',
      name: '中石化债',
      price: 100.80,
      change: 0.15,
      changePercent: 0.15,
      yield: 3.28,
      maturity: '2029-09-20',
      rating: 'AAA',
    },
  ],
  convertible: [
    {
      code: '113050',
      name: '南银转债',
      price: 128.56,
      change: 2.35,
      changePercent: 1.86,
      yield: -5.23,
      maturity: '2029-12-25',
      rating: 'AAA',
      premium: 15.32,
    },
    {
      code: '127045',
      name: '希望转2',
      price: 135.20,
      change: -1.80,
      changePercent: -1.31,
      yield: -8.45,
      maturity: '2028-08-18',
      rating: 'AA+',
      premium: 22.45,
    },
  ],
};

const Bond: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('treasury');
  const [favoriteList, setFavoriteList] = useState<string[]>(['019701', '113050']);

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

  const getRatingColor = (rating: string) => {
    if (rating === 'AAA') return 'gold';
    if (rating === 'AA+') return 'orange';
    if (rating === 'AA') return 'blue';
    return 'default';
  };

  const columns = [
    {
      title: '代码/名称',
      key: 'bond',
      render: (_: any, record: any) => (
        <div className={styles.bondInfo}>
          <span className={styles.bondName}>{record.name}</span>
          <span className={styles.bondCode}>{record.code}</span>
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
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      align: 'right' as const,
      render: (percent: number) => (
        <span className={getChangeColor(percent)}>{formatChange(percent)}%</span>
      ),
    },
    {
      title: '到期收益率',
      dataIndex: 'yield',
      key: 'yield',
      align: 'right' as const,
      render: (val: number) => <span>{val.toFixed(2)}%</span>,
    },
    {
      title: '到期日',
      dataIndex: 'maturity',
      key: 'maturity',
      align: 'center' as const,
    },
    {
      title: '评级',
      dataIndex: 'rating',
      key: 'rating',
      align: 'center' as const,
      render: (rating: string) => (
        <Tag color={getRatingColor(rating)}>{rating}</Tag>
      ),
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

  const categoryTabItems = bondCategories.map((cat) => ({
    key: cat.key,
    label: cat.label,
    children: (
      <Table
        columns={columns}
        dataSource={mockBondData[cat.key]}
        rowKey="code"
        pagination={false}
        className={styles.bondTable}
      />
    ),
  }));

  return (
    <div className={styles.bondPage}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>债券市场</h1>
      </div>

      {/* 国债收益率曲线卡片 */}
      <Card className={styles.yieldCurveCard}>
        <div className={styles.sectionTitle}>
          <span>中国国债收益率</span>
          <span className={styles.updateTime}>更新于 2024-01-19 15:30</span>
        </div>
        <Row gutter={[16, 16]} className={styles.yieldItems}>
          {treasuryYields.map((item) => (
            <Col xs={12} sm={8} md={4} key={item.term}>
              <div className={styles.yieldItem}>
                <span className={styles.yieldTerm}>{item.term}</span>
                <span className={`${styles.yieldValue} ${getChangeColor(item.change)}`}>
                  {item.yield.toFixed(2)}%
                </span>
                <span className={`${styles.yieldChange} ${getChangeColor(item.change)}`}>
                  {item.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  {Math.abs(item.change).toFixed(2)}bp
                </span>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 10年期国债收益率趋势 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card className={styles.highlightCard}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>中国10年期国债</span>
              <Tag color="blue">基准利率</Tag>
            </div>
            <Statistic
              value={2.68}
              precision={2}
              suffix="%"
              valueStyle={{
                fontSize: '32px',
                fontWeight: 700,
                fontFamily: "'SF Mono', 'Monaco', 'Consolas', monospace",
                color: 'var(--rise-color)',
              }}
            />
            <div className={styles.changeRow}>
              <span className="rise-text">
                <ArrowUpOutlined /> +0.01
              </span>
              <span className={styles.prevValue}>前值: 2.67%</span>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card className={styles.highlightCard}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>中美利差</span>
              <Tag color="orange">倒挂</Tag>
            </div>
            <Statistic
              value={-1.85}
              precision={2}
              suffix="%"
              valueStyle={{
                fontSize: '32px',
                fontWeight: 700,
                fontFamily: "'SF Mono', 'Monaco', 'Consolas', monospace",
                color: 'var(--fall-color)',
              }}
            />
            <div className={styles.changeRow}>
              <span className="fall-text">
                <FallOutlined /> 美债10Y: 4.53%
              </span>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 债券列表 */}
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

export default Bond;
