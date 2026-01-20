import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Card, 
  Table, 
  Input, 
  Button, 
  Space, 
  Empty, 
  Tag, 
  Tabs, 
  Modal, 
  List,
  message,
  Spin,
  Segmented,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  StarOutlined,
  StarFilled,
  DeleteOutlined,
  ReloadOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import * as echarts from 'echarts';
import styles from './index.less';
import { marketApi, stockApi } from '@/services/api';

// 时间范围选项
const TIME_RANGES = [
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 },
  { label: '半年', value: 180 },
  { label: '1年', value: 365 },
];

const { Search } = Input;

// 市场配置
const MARKETS = {
  CN: {
    name: 'A股',
    indices: [
      { code: 'SSE', name: '上证指数' },
      { code: 'SZSE', name: '深证成指' },
      { code: 'ChiNext', name: '创业板指' },
    ],
  },
  HK: {
    name: '港股',
    indices: [
      { code: 'HSI', name: '恒生指数' },
      { code: 'HSCEI', name: '恒生国企' },
      { code: 'HSTECH', name: '恒生科技' },
    ],
  },
  US: {
    name: '美股',
    indices: [
      { code: 'DJI', name: '道琼斯' },
      { code: 'IXIC', name: '纳斯达克' },
      { code: 'SPX', name: '标普500' },
    ],
  },
};

// 股票数据类型
interface StockData {
  code: string;
  name: string;
  market: string;
  price: number;
  change: number;
  changePercent: number;
  open?: number;
  high?: number;
  low?: number;
  volume?: number;
  amount?: number;
  turnover?: number;      // 换手率
  pe_ratio?: number;      // 市盈率
  pb_ratio?: number;      // 市净率
  market_cap?: number;    // 市值（亿）
  isFavorite?: boolean;
  // 迷你图数据
  historyData?: number[];
}

// 指数数据类型
interface IndexData {
  symbol: string;
  name: string;
  close: number;
  change: number;
  change_percent: number;
  time?: string;
}

// 搜索结果类型
interface SearchResult {
  code: string;
  name: string;
  market: string;
}

const Stock: React.FC = () => {
  // 当前市场
  const [activeMarket, setActiveMarket] = useState<string>('CN');
  
  // 时间范围（天数）
  const [timeRange, setTimeRange] = useState<number>(30);
  
  // 指数数据
  const [indicesData, setIndicesData] = useState<{ [key: string]: IndexData[] }>({
    CN: [],
    HK: [],
    US: [],
  });
  const [indicesLoading, setIndicesLoading] = useState(false);
  
  // 指数历史数据（用于折线图）
  const [indexHistory, setIndexHistory] = useState<{ [key: string]: any[] }>({});
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // 自选股数据
  const [watchlist, setWatchlist] = useState<StockData[]>([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  
  // 搜索相关
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // 图表 ref
  const chartRefs = useRef<{ [key: string]: echarts.ECharts }>({});
  const chartContainerRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // 格式化价格
  const formatPrice = (value: number) => {
    return value?.toLocaleString('zh-CN', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }) || '0.00';
  };

  // 格式化涨跌
  const formatChange = (value: number) => {
    if (value > 0) return `+${formatPrice(value)}`;
    return formatPrice(value);
  };

  // 格式化涨跌幅
  const formatPercent = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}%`;
    return `${value.toFixed(2)}%`;
  };

  // 获取涨跌颜色
  const getChangeColor = (value: number) => {
    if (value > 0) return 'rise';
    if (value < 0) return 'fall';
    return 'flat';
  };

  // 获取指数实时数据
  const fetchIndicesData = useCallback(async (market: string) => {
    setIndicesLoading(true);
    try {
      const marketConfig = MARKETS[market as keyof typeof MARKETS];
      const codes = marketConfig.indices.map(idx => idx.code);
      const data = await marketApi.getIndices(market, codes);
      
      if (data && data.length > 0) {
        setIndicesData(prev => ({
          ...prev,
          [market]: data.map((item: any) => ({
            symbol: item.symbol,
            name: item.name,
            close: item.close || 0,
            change: item.change || 0,
            change_percent: item.change_percent || 0,
            time: item.time,
          })),
        }));
      }
    } catch (error) {
      console.error(`获取${market}指数数据失败:`, error);
    }
    setIndicesLoading(false);
  }, []);

  // 获取指数历史数据
  const fetchIndexHistory = useCallback(async (market: string, symbol: string, days: number) => {
    try {
      const data = await stockApi.getIndexHistory(market, symbol, days);
      if (data && data.length > 0) {
        setIndexHistory(prev => ({
          ...prev,
          [`${market}_${symbol}`]: data,
        }));
      }
    } catch (error) {
      console.error(`获取${symbol}历史数据失败:`, error);
    }
  }, []);

  // 获取所有指数的历史数据
  const fetchAllIndexHistory = useCallback(async (market: string, days: number) => {
    setHistoryLoading(true);
    const marketConfig = MARKETS[market as keyof typeof MARKETS];
    await Promise.all(
      marketConfig.indices.map(idx => fetchIndexHistory(market, idx.code, days))
    );
    setHistoryLoading(false);
  }, [fetchIndexHistory]);

  // 获取自选股列表
  const fetchWatchlist = useCallback(async (market: string, refresh: boolean = false) => {
    setWatchlistLoading(true);
    try {
      const data = await stockApi.getWatchlist(market, refresh);
      if (data) {
        // 后端已经返回完整数据（包括走势图数据），直接使用
        const stocks = data.map((item: any) => ({
          code: item.code,
          name: item.name,
          market: item.market,
          price: item.price || item.close || 0,
          change: item.change || 0,
          changePercent: item.change_percent || item.changePercent || 0,
          open: item.open || 0,
          high: item.high || 0,
          low: item.low || 0,
          volume: item.volume || 0,
          amount: item.amount || 0,
          turnover: item.turnover || 0,
          pe_ratio: item.pe_ratio || 0,
          pb_ratio: item.pb_ratio || 0,
          market_cap: item.market_cap || 0,
          isFavorite: true,
          // 直接使用后端返回的走势图数据
          historyData: item.history_data || [],
        }));
        setWatchlist(stocks);
      }
    } catch (error) {
      console.error('获取自选股失败:', error);
    }
    setWatchlistLoading(false);
  }, []);

  // 搜索股票
  const handleSearch = async (keyword: string) => {
    if (!keyword.trim()) {
      setSearchResults([]);
      return;
    }
    
    setSearchLoading(true);
    try {
      const data = await stockApi.search(keyword, activeMarket);
      setSearchResults(data || []);
    } catch (error) {
      console.error('搜索股票失败:', error);
      message.error('搜索失败，请重试');
    }
    setSearchLoading(false);
  };

  // 添加自选股
  const handleAddToWatchlist = async (stock: SearchResult) => {
    try {
      await stockApi.addToWatchlist(stock.code, stock.name, stock.market);
      message.success('添加成功');
      setSearchModalVisible(false);
      setSearchKeyword('');
      setSearchResults([]);
      fetchWatchlist(activeMarket);
    } catch (error) {
      console.error('添加自选失败:', error);
      message.error('添加失败，请重试');
    }
  };

  // 删除自选股
  const handleRemoveFromWatchlist = async (code: string) => {
    try {
      await stockApi.removeFromWatchlist(code);
      message.success('已移除');
      setWatchlist(prev => prev.filter(s => s.code !== code));
    } catch (error) {
      console.error('移除自选失败:', error);
      message.error('移除失败，请重试');
    }
  };

  // 初始化图表
  const initChart = useCallback((market: string, symbol: string, containerId: string) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    // 销毁旧图表
    if (chartRefs.current[containerId]) {
      chartRefs.current[containerId].dispose();
    }

    const chart = echarts.init(container);
    chartRefs.current[containerId] = chart;

    const historyKey = `${market}_${symbol}`;
    const historyData = indexHistory[historyKey] || [];

    // 生成模拟数据（如果没有历史数据）
    const chartData = historyData.length > 0 
      ? historyData.map((item: any) => ({
          date: item.date || item.time,
          value: item.close || item.value,
        }))
      : generateMockData();

    const option: echarts.EChartsOption = {
      grid: {
        left: '8%',
        right: '3%',
        top: '10%',
        bottom: '18%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: chartData.map((d: any) => d.date),
        axisLine: { 
          show: true,
          lineStyle: { color: 'rgba(148, 163, 184, 0.2)' },
        },
        axisTick: { show: false },
        axisLabel: { 
          show: true,
          color: 'rgba(148, 163, 184, 0.6)',
          fontSize: 10,
          interval: Math.floor(chartData.length / 5), // 显示约5个时间点
        },
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { 
          show: true,
          color: 'rgba(148, 163, 184, 0.6)',
          fontSize: 10,
          formatter: (value: number) => value.toLocaleString('zh-CN', { maximumFractionDigits: 0 }),
        },
        splitLine: { 
          show: true,
          lineStyle: { 
            color: 'rgba(148, 163, 184, 0.1)',
            type: 'dashed',
          },
        },
        scale: true,
      },
      series: [
        {
          type: 'line',
          data: chartData.map((d: any) => d.value),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: getLineColor(chartData),
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: getAreaColor(chartData, 0.3) },
              { offset: 1, color: getAreaColor(chartData, 0.05) },
            ]),
          },
        },
      ],
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0];
          return `${data.axisValue}<br/>${formatPrice(data.value)}`;
        },
        backgroundColor: 'rgba(30, 41, 59, 0.9)',
        borderColor: 'rgba(148, 163, 184, 0.2)',
        textStyle: { color: '#e2e8f0' },
      },
    };

    chart.setOption(option);

    // 响应式
    const resizeObserver = new ResizeObserver(() => {
      chart.resize();
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, [indexHistory]);

  // 生成模拟数据
  const generateMockData = () => {
    const data = [];
    const now = new Date();
    let value = 3000 + Math.random() * 1000;
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      value = value * (1 + (Math.random() - 0.5) * 0.02);
      data.push({
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        value: Math.round(value * 100) / 100,
      });
    }
    return data;
  };

  // 获取折线颜色
  const getLineColor = (data: any[]) => {
    if (data.length < 2) return '#3b82f6';
    const first = data[0]?.value || 0;
    const last = data[data.length - 1]?.value || 0;
    return last >= first ? '#22c55e' : '#ef4444';
  };

  // 获取面积颜色
  const getAreaColor = (data: any[], alpha: number) => {
    if (data.length < 2) return `rgba(59, 130, 246, ${alpha})`;
    const first = data[0]?.value || 0;
    const last = data[data.length - 1]?.value || 0;
    return last >= first 
      ? `rgba(34, 197, 94, ${alpha})` 
      : `rgba(239, 68, 68, ${alpha})`;
  };

  // 初始加载
  useEffect(() => {
    fetchIndicesData(activeMarket);
    fetchWatchlist(activeMarket);
    fetchAllIndexHistory(activeMarket, timeRange);
  }, [activeMarket, fetchIndicesData, fetchWatchlist, fetchAllIndexHistory, timeRange]);

  // 初始化图表
  useEffect(() => {
    const marketConfig = MARKETS[activeMarket as keyof typeof MARKETS];
    marketConfig.indices.forEach(idx => {
      const containerId = `chart-${activeMarket}-${idx.code}`;
      setTimeout(() => {
        initChart(activeMarket, idx.code, containerId);
      }, 100);
    });

    return () => {
      // 清理图表
      Object.values(chartRefs.current).forEach(chart => {
        chart?.dispose();
      });
    };
  }, [activeMarket, indexHistory, initChart]);

  // 格式化成交量
  const formatVolume = (volume: number) => {
    if (!volume) return '-';
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)}亿`;
    }
    if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)}万`;
    }
    return volume.toString();
  };

  // 格式化市值（已是亿为单位）
  const formatMarketCap = (cap: number) => {
    if (!cap) return '-';
    if (cap >= 10000) {
      return `${(cap / 10000).toFixed(2)}万亿`;
    }
    return `${cap.toFixed(2)}亿`;
  };

  // 渲染迷你走势图
  const renderMiniChart = (data: number[], changePercent: number) => {
    if (!data || data.length === 0) {
      return <span className={styles.miniChartPlaceholder}>-</span>;
    }
    
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const height = 24;
    const width = 60;
    const stepX = width / (data.length - 1 || 1);
    
    const points = data.map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');
    
    const color = changePercent >= 0 ? '#22c55e' : '#ef4444';
    
    return (
      <svg width={width} height={height} className={styles.miniChart}>
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
        />
      </svg>
    );
  };

  // 自选股表格列
  const columns = [
    {
      title: '代码/名称',
      key: 'stock',
      width: 140,
      render: (_: any, record: StockData) => (
        <div className={styles.stockInfo}>
          <span className={styles.stockName}>{record.name}</span>
          <span className={styles.stockCode}>
            {record.code}
            <Tag 
              color={record.market === 'CN' ? 'blue' : record.market === 'HK' ? 'green' : 'orange'} 
              className={styles.marketTag}
            >
              {record.market}
            </Tag>
          </span>
        </div>
      ),
    },
    {
      title: '走势',
      key: 'trend',
      width: 80,
      align: 'center' as const,
      render: (_: any, record: StockData) => renderMiniChart(record.historyData || [], record.changePercent),
    },
    {
      title: '最新价',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      align: 'right' as const,
      render: (price: number, record: StockData) => (
        <span className={`${styles.price} ${styles[getChangeColor(record.changePercent)]}`}>
          {formatPrice(price)}
        </span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'changePercent',
      key: 'changePercent',
      width: 90,
      align: 'right' as const,
      render: (percent: number) => (
        <span className={`${styles.changePercent} ${styles[getChangeColor(percent)]}`}>
          {formatPercent(percent)}
        </span>
      ),
    },
    {
      title: '今日高低',
      key: 'highLow',
      width: 120,
      align: 'center' as const,
      render: (_: any, record: StockData) => (
        <div className={styles.highLow}>
          <span className={styles.rise}>{formatPrice(record.high || 0)}</span>
          <span className={styles.divider}>/</span>
          <span className={styles.fall}>{formatPrice(record.low || 0)}</span>
        </div>
      ),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      width: 90,
      align: 'right' as const,
      render: (volume: number) => <span className={styles.dimText}>{formatVolume(volume)}</span>,
    },
    {
      title: '换手率',
      dataIndex: 'turnover',
      key: 'turnover',
      width: 80,
      align: 'right' as const,
      render: (turnover: number) => (
        <span className={styles.dimText}>{turnover ? `${(turnover * 100).toFixed(2)}%` : '-'}</span>
      ),
    },
    {
      title: '市盈率',
      dataIndex: 'pe_ratio',
      key: 'pe_ratio',
      width: 80,
      align: 'right' as const,
      render: (pe: number) => <span className={styles.dimText}>{pe ? pe.toFixed(2) : '-'}</span>,
    },
    {
      title: '市值',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 90,
      align: 'right' as const,
      render: (cap: number) => <span className={styles.dimText}>{formatMarketCap(cap)}</span>,
    },
    {
      title: '操作',
      key: 'action',
      align: 'center' as const,
      width: 60,
      render: (_: any, record: StockData) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRemoveFromWatchlist(record.code)}
        />
      ),
    },
  ];

  // 渲染指数卡片
  const renderIndexCards = () => {
    const marketConfig = MARKETS[activeMarket as keyof typeof MARKETS];
    const currentIndices = indicesData[activeMarket] || [];

    return (
      <div className={styles.indicesGrid}>
        {marketConfig.indices.map((idx) => {
          const indexData = currentIndices.find(
            (d) => d.symbol === idx.code
          ) || {
            symbol: idx.code,
            name: idx.name,
            close: 0,
            change: 0,
            change_percent: 0,
          };

          return (
            <Card key={idx.code} className={styles.indexCard} bordered={false}>
              <div className={styles.indexHeader}>
                <div className={styles.indexInfo}>
                  <span className={styles.indexName}>{indexData.name}</span>
                  <span className={`${styles.indexPrice} ${styles[getChangeColor(indexData.change_percent)]}`}>
                    {formatPrice(indexData.close)}
                  </span>
                </div>
                <div className={`${styles.indexChange} ${styles[getChangeColor(indexData.change_percent)]}`}>
                  <span>{formatChange(indexData.change)}</span>
                  <span>{formatPercent(indexData.change_percent)}</span>
                </div>
              </div>
              <div 
                id={`chart-${activeMarket}-${idx.code}`}
                className={styles.indexChart}
              />
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <div className={styles.stockPage}>
      {/* 市场 Tab */}
      <Tabs
        activeKey={activeMarket}
        onChange={(key) => setActiveMarket(key)}
        className={styles.marketTabs}
        items={Object.entries(MARKETS).map(([key, value]) => ({
          key,
          label: (
            <span className={styles.tabLabel}>
              <LineChartOutlined />
              {value.name}
            </span>
          ),
        }))}
      />

      {/* 指数概览 */}
      <div className={styles.indicesSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            {MARKETS[activeMarket as keyof typeof MARKETS].name}指数
          </h2>
          <Space size="middle">
            <Segmented
              value={timeRange}
              onChange={(value) => setTimeRange(value as number)}
              options={TIME_RANGES}
              className={styles.timeRangeSelect}
            />
            <Button 
              type="text" 
              icon={<ReloadOutlined />}
              loading={indicesLoading || historyLoading}
              onClick={() => {
                fetchIndicesData(activeMarket);
                fetchAllIndexHistory(activeMarket, timeRange);
              }}
            >
              刷新
            </Button>
          </Space>
        </div>
        {indicesLoading && indicesData[activeMarket]?.length === 0 ? (
          <div className={styles.loadingContainer}>
            <Spin />
          </div>
        ) : (
          renderIndexCards()
        )}
      </div>

      {/* 自选股列表 */}
      <div className={styles.watchlistSection}>
        <div className={styles.sectionHeader}>
          <div className={styles.titleGroup}>
            <h2 className={styles.sectionTitle}>
              自选股票
              <span className={styles.stockCount}>({watchlist.length})</span>
            </h2>
          </div>
          <Space>
            <Button 
              type="text" 
              icon={<ReloadOutlined />}
              loading={watchlistLoading}
              onClick={() => fetchWatchlist(activeMarket, true)}
            >
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setSearchModalVisible(true)}
            >
              添加股票
            </Button>
          </Space>
        </div>

        <Card className={styles.watchlistCard} bordered={false}>
          {watchlist.length > 0 ? (
            <Table
              columns={columns}
              dataSource={watchlist}
              rowKey="code"
              pagination={false}
              loading={watchlistLoading}
              className={styles.stockTable}
            />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无自选股票"
            >
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setSearchModalVisible(true)}
              >
                添加股票
              </Button>
            </Empty>
          )}
        </Card>
      </div>

      {/* 搜索股票弹窗 */}
      <Modal
        title="添加股票"
        open={searchModalVisible}
        onCancel={() => {
          setSearchModalVisible(false);
          setSearchKeyword('');
          setSearchResults([]);
        }}
        footer={null}
        width={500}
        className={styles.searchModal}
      >
        <Search
          placeholder="输入股票代码或名称搜索"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
          loading={searchLoading}
          className={styles.searchInput}
        />
        
        <div className={styles.searchResults}>
          {searchLoading ? (
            <div className={styles.loadingContainer}>
              <Spin />
            </div>
          ) : searchResults.length > 0 ? (
            <List
              dataSource={searchResults}
              renderItem={(item) => (
                <List.Item
                  className={styles.searchResultItem}
                  actions={[
                    <Button
                      key="add"
                      type="link"
                      icon={<PlusOutlined />}
                      onClick={() => handleAddToWatchlist(item)}
                    >
                      添加
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <span>
                        {item.name}
                        <Tag color="blue" className={styles.resultTag}>
                          {item.market}
                        </Tag>
                      </span>
                    }
                    description={item.code}
                  />
                </List.Item>
              )}
            />
          ) : searchKeyword ? (
            <Empty description="未找到相关股票" />
          ) : (
            <div className={styles.searchTip}>
              请输入股票代码或名称进行搜索
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Stock;
