import React, { useState } from 'react';
import { Card, Table, Input, Button, Space, Empty, Tag } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  StarOutlined,
  StarFilled,
  DeleteOutlined,
} from '@ant-design/icons';
import styles from './index.less';

const { Search } = Input;

// 模拟数据 - 后续从API获取
const mockStockList = [
  {
    code: '600519',
    name: '贵州茅台',
    market: 'SH',
    price: 1688.88,
    change: 23.45,
    changePercent: 1.41,
    volume: '3.2万手',
    amount: '54.3亿',
    isFavorite: true,
  },
  {
    code: '000858',
    name: '五粮液',
    market: 'SZ',
    price: 168.52,
    change: -2.18,
    changePercent: -1.28,
    volume: '8.5万手',
    amount: '14.3亿',
    isFavorite: true,
  },
  {
    code: '601318',
    name: '中国平安',
    market: 'SH',
    price: 45.32,
    change: 0.56,
    changePercent: 1.25,
    volume: '15.2万手',
    amount: '6.9亿',
    isFavorite: false,
  },
];

const Stock: React.FC = () => {
  const [stockList, setStockList] = useState(mockStockList);
  const [searchValue, setSearchValue] = useState('');

  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise-text';
    if (value < 0) return 'fall-text';
    return '';
  };

  const formatChange = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}`;
    return value.toFixed(2);
  };

  const handleSearch = (value: string) => {
    console.log('搜索股票:', value);
    // TODO: 调用API搜索股票
  };

  const handleToggleFavorite = (code: string) => {
    setStockList((prev) =>
      prev.map((stock) =>
        stock.code === code ? { ...stock, isFavorite: !stock.isFavorite } : stock
      )
    );
  };

  const handleDelete = (code: string) => {
    setStockList((prev) => prev.filter((stock) => stock.code !== code));
  };

  const columns = [
    {
      title: '代码/名称',
      key: 'stock',
      render: (_: any, record: any) => (
        <div className={styles.stockInfo}>
          <span className={styles.stockName}>{record.name}</span>
          <span className={styles.stockCode}>
            {record.code}
            <Tag color={record.market === 'SH' ? 'blue' : 'orange'} className={styles.marketTag}>
              {record.market}
            </Tag>
          </span>
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
      title: '涨跌额',
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
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      align: 'right' as const,
    },
    {
      title: '成交额',
      dataIndex: 'amount',
      key: 'amount',
      align: 'right' as const,
    },
    {
      title: '操作',
      key: 'action',
      align: 'center' as const,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="text"
            icon={record.isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={() => handleToggleFavorite(record.code)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.code)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div className={styles.stockPage}>
      {/* 页面标题和操作栏 */}
      <div className={styles.pageHeader}>
        <div className={styles.titleSection}>
          <h1 className={styles.pageTitle}>自选股票</h1>
          <span className={styles.stockCount}>共 {stockList.length} 只</span>
        </div>
        <div className={styles.actionSection}>
          <Search
            placeholder="搜索股票代码/名称"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            onChange={(e) => setSearchValue(e.target.value)}
            className={styles.searchInput}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            添加股票
          </Button>
        </div>
      </div>

      {/* 自选股列表 */}
      <Card className={styles.stockCard}>
        {stockList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={stockList}
            rowKey="code"
            pagination={false}
            className={styles.stockTable}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无自选股票"
          >
            <Button type="primary" icon={<PlusOutlined />}>
              添加股票
            </Button>
          </Empty>
        )}
      </Card>
    </div>
  );
};

export default Stock;
