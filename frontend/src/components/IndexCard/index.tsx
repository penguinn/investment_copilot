import React from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import styles from './index.less';

interface IndexCardProps {
  market: string;
  data: any;
  title: string;
  onSelect: (market: string, index: string) => void;
}

export const IndexCard: React.FC<IndexCardProps> = ({
  market,
  data,
  title,
  onSelect,
}) => {
  const getColor = (change: number) => (change >= 0 ? '#cf1322' : '#3f8600');

  return (
    <Card
      title={title}
      className={styles.indexCard}
      hoverable
      onClick={() => onSelect(market, data?.symbol)}
    >
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Statistic
            title={data?.name}
            value={data?.items?.[0]?.close}
            precision={2}
            valueStyle={{ color: getColor(data?.items?.[0]?.change || 0) }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="涨跌幅"
            value={data?.items?.[0]?.change_percent}
            precision={2}
            prefix={data?.items?.[0]?.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            suffix="%"
            valueStyle={{ color: getColor(data?.items?.[0]?.change || 0) }}
          />
        </Col>
      </Row>
    </Card>
  );
}; 