import React from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import styles from './index.less';

interface GoldCardProps {
  data: any;
}

export const GoldCard: React.FC<GoldCardProps> = ({ data }) => {
  const getColor = (change: number) => (change >= 0 ? '#cf1322' : '#3f8600');

  return (
    <Card title="黄金市场" className={styles.goldCard}>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card className={styles.innerCard}>
            <Statistic
              title="沪金99.99"
              value={data?.AU9999?.price}
              precision={2}
              valueStyle={{ color: getColor(data?.AU9999?.change || 0) }}
              suffix="元/克"
            />
            <Statistic
              value={data?.AU9999?.change_percent}
              precision={2}
              prefix={data?.AU9999?.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="%"
              valueStyle={{ color: getColor(data?.AU9999?.change || 0) }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card className={styles.innerCard}>
            <Statistic
              title="伦敦金"
              value={data?.XAU?.price}
              precision={2}
              valueStyle={{ color: getColor(data?.XAU?.change || 0) }}
              suffix="美元/盎司"
            />
            <Statistic
              value={data?.XAU?.change_percent}
              precision={2}
              prefix={data?.XAU?.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="%"
              valueStyle={{ color: getColor(data?.XAU?.change || 0) }}
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );
}; 