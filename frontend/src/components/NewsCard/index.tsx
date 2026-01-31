import React, { useState, useEffect, useCallback } from 'react';
import { Card, List, Tag, Tabs, Empty, Spin, Button } from 'antd';
import { ReloadOutlined, BellOutlined, FileTextOutlined, ThunderboltOutlined } from '@ant-design/icons';
import styles from './index.less';
import { newsApi } from '@/services/api';

// 来源颜色映射
const sourceColors: Record<string, string> = {
  cls: 'orange',
  eastmoney: 'blue',
  pbc: 'red',
  csrc: 'purple',
  ndrc: 'green',
  stats: 'cyan',
  miit: 'geekblue',
};

// 来源名称映射
const sourceNames: Record<string, string> = {
  cls: '财联社',
  eastmoney: '东财',
  pbc: '央行',
  csrc: '证监会',
  ndrc: '发改委',
  stats: '统计局',
  miit: '工信部',
};

interface NewsItem {
  id: number;
  source: string;
  source_name: string;
  title: string;
  content: string;
  summary?: string;
  url?: string;
  category: string;
  importance: number;
  related_sectors?: string;
  publish_time: string;
}

interface NewsCardProps {
  height?: number | string;
}

const NewsCard: React.FC<NewsCardProps> = ({ height = 400 }) => {
  const [activeTab, setActiveTab] = useState('market');
  const [marketNews, setMarketNews] = useState<NewsItem[]>([]);
  const [policyNews, setPolicyNews] = useState<NewsItem[]>([]);
  const [importantNews, setImportantNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 格式化时间
  const formatTime = (timeStr: string) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
  };

  // 获取市场快讯
  const fetchMarketNews = useCallback(async () => {
    try {
      const data = await newsApi.getMarket(30);
      if (data) setMarketNews(data);
    } catch (error) {
      console.error('获取市场快讯失败:', error);
    }
  }, []);

  // 获取政策新闻
  const fetchPolicyNews = useCallback(async () => {
    try {
      const data = await newsApi.getPolicy(20);
      if (data) setPolicyNews(data);
    } catch (error) {
      console.error('获取政策新闻失败:', error);
    }
  }, []);

  // 获取重要新闻
  const fetchImportantNews = useCallback(async () => {
    try {
      const data = await newsApi.getImportant(3, 24, 20);
      if (data) setImportantNews(data);
    } catch (error) {
      console.error('获取重要新闻失败:', error);
    }
  }, []);

  // 刷新数据
  const handleRefresh = async () => {
    setLoading(true);
    await Promise.all([
      fetchMarketNews(),
      fetchPolicyNews(),
      fetchImportantNews(),
    ]);
    setLoading(false);
  };

  // 初始化
  useEffect(() => {
    handleRefresh();
    
    // 每 2 分钟自动刷新
    const interval = setInterval(handleRefresh, 120000);
    return () => clearInterval(interval);
  }, [fetchMarketNews, fetchPolicyNews, fetchImportantNews]);

  // 渲染新闻列表项
  const renderNewsItem = (item: NewsItem) => (
    <List.Item
      className={`${styles.newsItem} ${item.importance >= 4 ? styles.important : ''}`}
      onClick={() => item.url && window.open(item.url, '_blank')}
    >
      <div className={styles.newsContent}>
        <div className={styles.newsHeader}>
          <Tag color={sourceColors[item.source] || 'default'} className={styles.sourceTag}>
            {sourceNames[item.source] || item.source_name}
          </Tag>
          <span className={styles.newsTime}>{formatTime(item.publish_time)}</span>
          {item.importance >= 4 && (
            <Tag color="red" className={styles.importanceTag}>重要</Tag>
          )}
        </div>
        <div className={styles.newsTitle}>
          {item.title || item.content.substring(0, 80)}
        </div>
        {item.related_sectors && (
          <div className={styles.sectors}>
            {item.related_sectors.split(',').map(sector => (
              <Tag key={sector} className={styles.sectorTag}>{sector}</Tag>
            ))}
          </div>
        )}
      </div>
    </List.Item>
  );

  // 当前 Tab 的数据
  const getCurrentData = () => {
    switch (activeTab) {
      case 'market':
        return marketNews;
      case 'policy':
        return policyNews;
      case 'important':
        return importantNews;
      default:
        return [];
    }
  };

  return (
    <Card
      className={styles.newsCard}
      title={
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>
            <BellOutlined className={styles.cardIcon} />
            资讯快报
          </span>
          <Button
            type="text"
            icon={<ReloadOutlined spin={loading} />}
            onClick={handleRefresh}
            className={styles.refreshBtn}
          />
        </div>
      }
      bordered={false}
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className={styles.newsTabs}
        items={[
          {
            key: 'market',
            label: (
              <span>
                <ThunderboltOutlined />
                市场快讯
              </span>
            ),
          },
          {
            key: 'policy',
            label: (
              <span>
                <FileTextOutlined />
                政策公告
              </span>
            ),
          },
          {
            key: 'important',
            label: (
              <span>
                <BellOutlined />
                重要资讯
              </span>
            ),
          },
        ]}
      />

      <div className={styles.newsList} style={{ height: typeof height === 'number' ? height - 100 : height }}>
        {loading ? (
          <div className={styles.loadingContainer}>
            <Spin />
          </div>
        ) : getCurrentData().length > 0 ? (
          <List
            dataSource={getCurrentData()}
            renderItem={renderNewsItem}
            split={false}
          />
        ) : (
          <Empty description="暂无新闻数据" className={styles.empty} />
        )}
      </div>
    </Card>
  );
};

export default NewsCard;
