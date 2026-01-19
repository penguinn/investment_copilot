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

// 基金类型标签颜色
const fundTypeColors: Record<string, string> = {
  '股票型': 'red',
  '混合型': 'orange',
  '债券型': 'blue',
  '指数型': 'purple',
  '货币型': 'green',
  'QDII': 'cyan',
};

// 模拟数据
const mockFundList = [
  {
    code: '519736',
    name: '交银新成长混合',
    type: '混合型',
    nav: 2.8845,
    accNav: 3.2145,
    change: 1.25,
    return1m: 5.67,
    return1y: 28.34,
    isFavorite: true,
  },
  {
    code: '110011',
    name: '易方达优质精选混合',
    type: '混合型',
    nav: 8.5632,
    accNav: 8.9832,
    change: -0.86,
    return1m: -2.34,
    return1y: 15.67,
    isFavorite: true,
  },
  {
    code: '510300',
    name: '华泰柏瑞沪深300ETF',
    type: '指数型',
    nav: 4.2315,
    accNav: 4.2315,
    change: 0.45,
    return1m: 3.21,
    return1y: 8.56,
    isFavorite: false,
  },
];

const Fund: React.FC = () => {
  const [fundList, setFundList] = useState(mockFundList);
  const [searchValue, setSearchValue] = useState('');

  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise-text';
    if (value < 0) return 'fall-text';
    return '';
  };

  const formatChange = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}%`;
    return `${value.toFixed(2)}%`;
  };

  const handleSearch = (value: string) => {
    console.log('搜索基金:', value);
  };

  const handleToggleFavorite = (code: string) => {
    setFundList((prev) =>
      prev.map((fund) =>
        fund.code === code ? { ...fund, isFavorite: !fund.isFavorite } : fund
      )
    );
  };

  const handleDelete = (code: string) => {
    setFundList((prev) => prev.filter((fund) => fund.code !== code));
  };

  const columns = [
    {
      title: '代码/名称',
      key: 'fund',
      render: (_: any, record: any) => (
        <div className={styles.fundInfo}>
          <span className={styles.fundName}>{record.name}</span>
          <span className={styles.fundCode}>
            {record.code}
            <Tag color={fundTypeColors[record.type]} className={styles.fundTypeTag}>
              {record.type}
            </Tag>
          </span>
        </div>
      ),
    },
    {
      title: '最新净值',
      dataIndex: 'nav',
      key: 'nav',
      align: 'right' as const,
      render: (nav: number, record: any) => (
        <span className={`${styles.nav} ${getChangeColor(record.change)}`}>
          {nav.toFixed(4)}
        </span>
      ),
    },
    {
      title: '累计净值',
      dataIndex: 'accNav',
      key: 'accNav',
      align: 'right' as const,
      render: (accNav: number) => <span>{accNav.toFixed(4)}</span>,
    },
    {
      title: '日涨跌',
      dataIndex: 'change',
      key: 'change',
      align: 'right' as const,
      render: (change: number) => (
        <span className={`${styles.changePercent} ${getChangeColor(change)}`}>
          {formatChange(change)}
        </span>
      ),
    },
    {
      title: '近1月',
      dataIndex: 'return1m',
      key: 'return1m',
      align: 'right' as const,
      render: (value: number) => (
        <span className={getChangeColor(value)}>{formatChange(value)}</span>
      ),
    },
    {
      title: '近1年',
      dataIndex: 'return1y',
      key: 'return1y',
      align: 'right' as const,
      render: (value: number) => (
        <span className={getChangeColor(value)}>{formatChange(value)}</span>
      ),
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
    <div className={styles.fundPage}>
      <div className={styles.pageHeader}>
        <div className={styles.titleSection}>
          <h1 className={styles.pageTitle}>自选基金</h1>
          <span className={styles.fundCount}>共 {fundList.length} 只</span>
        </div>
        <div className={styles.actionSection}>
          <Search
            placeholder="搜索基金代码/名称"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            onChange={(e) => setSearchValue(e.target.value)}
            className={styles.searchInput}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            添加基金
          </Button>
        </div>
      </div>

      <Card className={styles.fundCard}>
        {fundList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={fundList}
            rowKey="code"
            pagination={false}
            className={styles.fundTable}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无自选基金"
          >
            <Button type="primary" icon={<PlusOutlined />}>
              添加基金
            </Button>
          </Empty>
        )}
      </Card>
    </div>
  );
};

export default Fund;
