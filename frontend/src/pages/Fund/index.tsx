import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Table, Button, Space, Empty, Tag, Tabs, Modal, Input, List, message, Segmented, Descriptions, Spin } from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  SearchOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import * as echarts from 'echarts';
import styles from './index.less';
import { etfApi, otcFundApi } from '@/services/api';

// ETF 类型标签颜色
const etfTypeColors: Record<string, string> = {
  '宽基ETF': 'blue',
  '行业ETF': 'orange',
  '跨境ETF': 'purple',
  '债券ETF': 'green',
  '商品ETF': 'gold',
  '其他ETF': 'default',
};

// 场外基金类型标签颜色
const fundTypeColors: Record<string, string> = {
  '股票型': 'red',
  '混合型': 'orange',
  '债券型': 'blue',
  '指数型': 'purple',
  'QDII': 'cyan',
};

// 热门 ETF 配置
const HOT_ETFS = [
  { code: '510300', name: '沪深300ETF' },
  { code: '510500', name: '中证500ETF' },
  { code: '159915', name: '创业板ETF' },
  { code: '588000', name: '科创50ETF' },
];

// 时间范围选项
const TIME_RANGES = [
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 },
];

// 排序选项
const SORT_OPTIONS = [
  { label: '近1年', value: 'return_1y' },
  { label: '近6月', value: 'return_6m' },
  { label: '近3月', value: 'return_3m' },
  { label: '近1月', value: 'return_1m' },
  { label: '今年来', value: 'return_ytd' },
];

// 场外基金类型
const OTC_FUND_TYPES = ['全部', '股票型', '混合型', '债券型', '指数型', 'QDII'];

interface ETFData {
  code: string;
  name: string;
  etf_type: string;
  price: number;
  change: number;
  change_percent: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  history_data?: number[];
}

interface OTCFundData {
  code: string;
  name: string;
  fund_type: string;
  nav: number;
  acc_nav: number;
  change_percent: number;
  return_1w: number;
  return_1m: number;
  return_3m: number;
  return_6m: number;
  return_1y: number;
  return_ytd: number;
  history_data?: number[];
}

const Fund: React.FC = () => {
  // Tab 状态
  const [activeTab, setActiveTab] = useState<'etf' | 'otc'>('etf');
  
  // ==================== ETF 状态 ====================
  const [timeRange, setTimeRange] = useState(30);
  const [hotEtfs, setHotEtfs] = useState<ETFData[]>([]);
  const [hotLoading, setHotLoading] = useState(false);
  const [etfWatchlist, setEtfWatchlist] = useState<ETFData[]>([]);
  const [etfWatchlistLoading, setEtfWatchlistLoading] = useState(false);
  const [etfSearchModalVisible, setEtfSearchModalVisible] = useState(false);
  const [etfSearchKeyword, setEtfSearchKeyword] = useState('');
  const [etfSearchResults, setEtfSearchResults] = useState<ETFData[]>([]);
  const [etfSearchLoading, setEtfSearchLoading] = useState(false);
  
  // ==================== 场外基金状态 ====================
  const [otcFundType, setOtcFundType] = useState('全部');
  const [otcSortBy, setOtcSortBy] = useState('return_1y');
  const [otcRanking, setOtcRanking] = useState<OTCFundData[]>([]);
  const [otcRankingLoading, setOtcRankingLoading] = useState(false);
  const [otcWatchlist, setOtcWatchlist] = useState<OTCFundData[]>([]);
  const [otcWatchlistLoading, setOtcWatchlistLoading] = useState(false);
  const [otcSearchModalVisible, setOtcSearchModalVisible] = useState(false);
  const [otcSearchKeyword, setOtcSearchKeyword] = useState('');
  const [otcSearchResults, setOtcSearchResults] = useState<OTCFundData[]>([]);
  const [otcSearchLoading, setOtcSearchLoading] = useState(false);
  
  // 基金详情弹窗
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [fundDetail, setFundDetail] = useState<any>(null);
  
  // 图表实例
  const chartRefs = useRef<Record<string, echarts.ECharts>>({});
  
  // ==================== 通用方法 ====================
  
  const formatChange = (value: number) => {
    if (value > 0) return `+${value.toFixed(2)}%`;
    return `${value.toFixed(2)}%`;
  };
  
  const getChangeClass = (value: number) => {
    if (value > 0) return styles.rise;
    if (value < 0) return styles.fall;
    return '';
  };
  
  const formatVolume = (value: number) => {
    if (value >= 100000000) return `${(value / 100000000).toFixed(2)}亿`;
    if (value >= 10000) return `${(value / 10000).toFixed(2)}万`;
    return value.toString();
  };
  
  const formatAmount = (value: number) => {
    if (value >= 100000000) return `${(value / 100000000).toFixed(2)}亿`;
    if (value >= 10000) return `${(value / 10000).toFixed(2)}万`;
    return value.toFixed(2);
  };

  // 渲染迷你走势图
  const renderMiniChart = (historyData: number[], isNav: boolean = false) => {
    if (!historyData || historyData.length < 2) return <span>-</span>;
    
    const firstValue = historyData[0];
    const lastValue = historyData[historyData.length - 1];
    const isUp = lastValue >= firstValue;
    const color = isUp ? '#22c55e' : '#ef4444';
    
    const min = Math.min(...historyData);
    const max = Math.max(...historyData);
    const range = max - min || 1;
    
    const width = 80;
    const height = 30;
    const points = historyData.map((v, i) => {
      const x = (i / (historyData.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');
    
    return (
      <svg width={width} height={height} className={styles.miniChart}>
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          points={points}
        />
      </svg>
    );
  };

  // ==================== ETF 方法 ====================

  const fetchHotEtfs = useCallback(async () => {
    setHotLoading(true);
    try {
      const data = await etfApi.getHot();
      if (data) setHotEtfs(data);
    } catch (error) {
      console.error('获取热门ETF失败:', error);
    }
    setHotLoading(false);
  }, []);

  const fetchEtfWatchlist = useCallback(async (refresh: boolean = false) => {
    setEtfWatchlistLoading(true);
    try {
      const data = await etfApi.getWatchlist(refresh);
      if (data) setEtfWatchlist(data);
    } catch (error) {
      console.error('获取ETF自选失败:', error);
    }
    setEtfWatchlistLoading(false);
  }, []);

  const initHotChart = useCallback(async (code: string, containerId: string) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (chartRefs.current[containerId]) {
      chartRefs.current[containerId].dispose();
    }

    const chart = echarts.init(container);
    chartRefs.current[containerId] = chart;

    try {
      const historyData = await etfApi.getHistory(code, timeRange);
      if (historyData && historyData.length > 0) {
        const firstClose = historyData[0].close;
        const lastClose = historyData[historyData.length - 1].close;
        const isUp = lastClose >= firstClose;

        const option: echarts.EChartsOption = {
          grid: { left: '8%', right: '3%', top: '10%', bottom: '18%', containLabel: true },
          xAxis: {
            type: 'category',
            data: historyData.map((d: any) => d.date),
            axisLine: { show: true, lineStyle: { color: 'rgba(148, 163, 184, 0.2)' } },
            axisTick: { show: false },
            axisLabel: { show: true, color: 'rgba(148, 163, 184, 0.6)', fontSize: 10, interval: Math.floor(historyData.length / 5) },
            boundaryGap: false,
          },
          yAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { show: true, color: 'rgba(148, 163, 184, 0.6)', fontSize: 10, formatter: (value: number) => value.toFixed(3) },
            splitLine: { show: true, lineStyle: { color: 'rgba(148, 163, 184, 0.1)', type: 'dashed' } },
            scale: true,
          },
          series: [{
            type: 'line',
            data: historyData.map((d: any) => d.close),
            smooth: true,
            symbol: 'none',
            lineStyle: { color: isUp ? '#22c55e' : '#ef4444', width: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: isUp ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)' },
                { offset: 1, color: isUp ? 'rgba(34, 197, 94, 0.05)' : 'rgba(239, 68, 68, 0.05)' },
              ]),
            },
          }],
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(30, 41, 59, 0.95)',
            borderColor: 'rgba(148, 163, 184, 0.2)',
            textStyle: { color: '#e2e8f0', fontSize: 12 },
            formatter: (params: any) => `${params[0].name}<br/>收盘价: ${params[0].value.toFixed(4)}`,
          },
        };

        chart.setOption(option);
      }
    } catch (error) {
      console.error(`获取ETF历史数据失败 ${code}:`, error);
    }
  }, [timeRange]);

  const handleEtfSearch = async (keyword: string) => {
    if (!keyword.trim()) { setEtfSearchResults([]); return; }
    setEtfSearchLoading(true);
    try {
      const data = await etfApi.search(keyword);
      setEtfSearchResults(data || []);
    } catch (error) {
      console.error('搜索ETF失败:', error);
      message.error('搜索失败');
    }
    setEtfSearchLoading(false);
  };

  const handleAddEtfToWatchlist = async (etf: ETFData) => {
    try {
      await etfApi.addToWatchlist(etf.code, etf.name);
      message.success('添加成功');
      setEtfSearchModalVisible(false);
      setEtfSearchKeyword('');
      setEtfSearchResults([]);
      fetchEtfWatchlist();
    } catch (error) {
      console.error('添加自选失败:', error);
      message.error('添加失败');
    }
  };

  const handleRemoveEtfFromWatchlist = async (code: string) => {
    try {
      await etfApi.removeFromWatchlist(code);
      message.success('移除成功');
      fetchEtfWatchlist();
    } catch (error) {
      console.error('移除自选失败:', error);
      message.error('移除失败');
    }
  };

  // ==================== 场外基金方法 ====================

  const fetchOtcRanking = useCallback(async () => {
    setOtcRankingLoading(true);
    try {
      const data = await otcFundApi.getRanking(
        otcFundType === '全部' ? undefined : otcFundType,
        otcSortBy,
        20
      );
      if (data) setOtcRanking(data);
    } catch (error) {
      console.error('获取基金排行失败:', error);
    }
    setOtcRankingLoading(false);
  }, [otcFundType, otcSortBy]);

  const fetchOtcWatchlist = useCallback(async (refresh: boolean = false) => {
    setOtcWatchlistLoading(true);
    try {
      const data = await otcFundApi.getWatchlist(refresh);
      if (data) setOtcWatchlist(data);
    } catch (error) {
      console.error('获取场外基金自选失败:', error);
    }
    setOtcWatchlistLoading(false);
  }, []);

  const handleOtcSearch = async (keyword: string) => {
    if (!keyword.trim()) { setOtcSearchResults([]); return; }
    setOtcSearchLoading(true);
    try {
      const data = await otcFundApi.search(keyword);
      setOtcSearchResults(data || []);
    } catch (error) {
      console.error('搜索基金失败:', error);
      message.error('搜索失败');
    }
    setOtcSearchLoading(false);
  };

  const handleAddOtcToWatchlist = async (fund: OTCFundData) => {
    try {
      await otcFundApi.addToWatchlist(fund.code, fund.name, fund.fund_type);
      message.success('添加成功');
      setOtcSearchModalVisible(false);
      setOtcSearchKeyword('');
      setOtcSearchResults([]);
      fetchOtcWatchlist();
    } catch (error) {
      console.error('添加自选失败:', error);
      message.error('添加失败');
    }
  };

  const handleRemoveOtcFromWatchlist = async (code: string) => {
    try {
      await otcFundApi.removeFromWatchlist(code);
      message.success('移除成功');
      fetchOtcWatchlist();
    } catch (error) {
      console.error('移除自选失败:', error);
      message.error('移除失败');
    }
  };

  const handleShowFundDetail = async (code: string) => {
    setDetailModalVisible(true);
    setDetailLoading(true);
    try {
      const data = await otcFundApi.getDetail(code);
      setFundDetail(data);
    } catch (error) {
      console.error('获取基金详情失败:', error);
      message.error('获取详情失败');
    }
    setDetailLoading(false);
  };

  // ==================== 表格列定义 ====================

  const etfWatchlistColumns = [
    {
      title: '代码/名称',
      key: 'etf',
      width: 200,
      render: (_: any, record: ETFData) => (
        <div className={styles.fundInfo}>
          <span className={styles.fundName}>{record.name}</span>
          <span className={styles.fundCode}>
            {record.code}
            <Tag color={etfTypeColors[record.etf_type] || 'default'} className={styles.fundTypeTag}>
              {record.etf_type}
            </Tag>
          </span>
        </div>
      ),
    },
    { title: '走势', key: 'trend', width: 100, align: 'center' as const, render: (_: any, record: ETFData) => renderMiniChart(record.history_data || []) },
    { title: '最新价', dataIndex: 'price', key: 'price', width: 100, align: 'right' as const, render: (price: number, record: ETFData) => <span className={getChangeClass(record.change_percent)}>{price.toFixed(4)}</span> },
    { title: '涨跌幅', dataIndex: 'change_percent', key: 'change_percent', width: 100, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '今日高低', key: 'highLow', width: 120, align: 'center' as const, render: (_: any, record: ETFData) => <span className={styles.highLow}>{record.high?.toFixed(4) || '-'} / {record.low?.toFixed(4) || '-'}</span> },
    { title: '成交量', dataIndex: 'volume', key: 'volume', width: 100, align: 'right' as const, render: (value: number) => formatVolume(value || 0) },
    { title: '操作', key: 'action', width: 80, align: 'center' as const, render: (_: any, record: ETFData) => <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleRemoveEtfFromWatchlist(record.code)} /> },
  ];

  const otcRankingColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: any, __: any, index: number) => <span className={styles.rank}>{index + 1}</span>,
    },
    {
      title: '代码/名称',
      key: 'fund',
      width: 200,
      render: (_: any, record: OTCFundData) => (
        <div className={styles.fundInfo}>
          <span className={styles.fundName}>{record.name}</span>
          <span className={styles.fundCode}>
            {record.code}
            <Tag color={fundTypeColors[record.fund_type] || 'default'} className={styles.fundTypeTag}>
              {record.fund_type}
            </Tag>
          </span>
        </div>
      ),
    },
    { title: '净值', dataIndex: 'nav', key: 'nav', width: 80, align: 'right' as const, render: (nav: number) => nav?.toFixed(4) || '-' },
    { title: '日涨跌', dataIndex: 'change_percent', key: 'change_percent', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '近1月', dataIndex: 'return_1m', key: 'return_1m', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '近1年', dataIndex: 'return_1y', key: 'return_1y', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    {
      title: '操作',
      key: 'action',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: OTCFundData) => (
        <Space>
          <Button type="text" icon={<InfoCircleOutlined />} onClick={() => handleShowFundDetail(record.code)} />
          <Button type="primary" size="small" onClick={() => handleAddOtcToWatchlist(record)}>添加</Button>
        </Space>
      ),
    },
  ];

  const otcWatchlistColumns = [
    {
      title: '代码/名称',
      key: 'fund',
      width: 200,
      render: (_: any, record: OTCFundData) => (
        <div className={styles.fundInfo}>
          <span className={styles.fundName}>{record.name}</span>
          <span className={styles.fundCode}>
            {record.code}
            <Tag color={fundTypeColors[record.fund_type] || 'default'} className={styles.fundTypeTag}>
              {record.fund_type}
            </Tag>
          </span>
        </div>
      ),
    },
    { title: '走势', key: 'trend', width: 100, align: 'center' as const, render: (_: any, record: OTCFundData) => renderMiniChart(record.history_data || [], true) },
    { title: '净值', dataIndex: 'nav', key: 'nav', width: 80, align: 'right' as const, render: (nav: number, record: OTCFundData) => <span className={getChangeClass(record.change_percent)}>{nav?.toFixed(4) || '-'}</span> },
    { title: '日涨跌', dataIndex: 'change_percent', key: 'change_percent', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '近1周', dataIndex: 'return_1w', key: 'return_1w', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '近1月', dataIndex: 'return_1m', key: 'return_1m', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    { title: '近1年', dataIndex: 'return_1y', key: 'return_1y', width: 80, align: 'right' as const, render: (value: number) => <span className={getChangeClass(value)}>{formatChange(value)}</span> },
    {
      title: '操作',
      key: 'action',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: OTCFundData) => (
        <Space>
          <Button type="text" icon={<InfoCircleOutlined />} onClick={() => handleShowFundDetail(record.code)} />
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleRemoveOtcFromWatchlist(record.code)} />
        </Space>
      ),
    },
  ];

  // ==================== Effects ====================

  useEffect(() => {
    if (activeTab === 'etf') {
      fetchHotEtfs();
      fetchEtfWatchlist();
    } else {
      fetchOtcRanking();
      fetchOtcWatchlist();
    }
  }, [activeTab, fetchHotEtfs, fetchEtfWatchlist, fetchOtcRanking, fetchOtcWatchlist]);

  useEffect(() => {
    if (activeTab === 'otc') {
      fetchOtcRanking();
    }
  }, [otcFundType, otcSortBy, activeTab, fetchOtcRanking]);

  useEffect(() => {
    if (activeTab === 'etf' && hotEtfs.length > 0) {
      HOT_ETFS.forEach(etf => {
        const containerId = `etf-chart-${etf.code}`;
        setTimeout(() => initHotChart(etf.code, containerId), 100);
      });
    }

    return () => {
      Object.values(chartRefs.current).forEach(chart => chart?.dispose());
      chartRefs.current = {};
    };
  }, [hotEtfs, initHotChart, activeTab]);

  useEffect(() => {
    if (activeTab === 'etf' && hotEtfs.length > 0) {
      HOT_ETFS.forEach(etf => initHotChart(etf.code, `etf-chart-${etf.code}`));
    }
  }, [timeRange, hotEtfs, initHotChart, activeTab]);

  useEffect(() => {
    const handleResize = () => Object.values(chartRefs.current).forEach(chart => chart?.resize());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className={styles.fundPage}>
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as 'etf' | 'otc')}
        className={styles.mainTabs}
        items={[
          { key: 'etf', label: '场内基金' },
          { key: 'otc', label: '场外基金' },
        ]}
      />

      {/* ==================== 场内基金 Tab ==================== */}
      {activeTab === 'etf' && (
        <>
          <div className={styles.hotSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>热门ETF行情</h2>
              <Space>
                <Segmented options={TIME_RANGES.map(t => ({ label: t.label, value: t.value }))} value={timeRange} onChange={(value) => setTimeRange(value as number)} className={styles.timeRangeSelect} />
                <Button icon={<ReloadOutlined />} loading={hotLoading} onClick={() => fetchHotEtfs()}>刷新</Button>
              </Space>
            </div>
            
            <div className={styles.hotEtfGrid}>
              {HOT_ETFS.map(etf => {
                const etfData = hotEtfs.find(e => e.code === etf.code);
                return (
                  <Card key={etf.code} className={styles.hotEtfCard} bordered={false}>
                    <div className={styles.etfHeader}>
                      <span className={styles.etfName}>{etf.name}</span>
                      <span className={styles.etfCode}>{etf.code}</span>
                    </div>
                    <div className={styles.etfPrice}>
                      <span className={`${styles.price} ${getChangeClass(etfData?.change_percent || 0)}`}>{etfData?.price?.toFixed(4) || '-'}</span>
                      <span className={`${styles.change} ${getChangeClass(etfData?.change_percent || 0)}`}>{etfData ? formatChange(etfData.change_percent) : '-'}</span>
                    </div>
                    <div id={`etf-chart-${etf.code}`} className={styles.etfChart}></div>
                  </Card>
                );
              })}
            </div>
          </div>

          <div className={styles.watchlistSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>自选ETF<span className={styles.fundCount}>({etfWatchlist.length})</span></h2>
              <Space>
                <Button icon={<ReloadOutlined />} loading={etfWatchlistLoading} onClick={() => fetchEtfWatchlist(true)}>刷新</Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setEtfSearchModalVisible(true)}>添加ETF</Button>
              </Space>
            </div>

            <Card className={styles.watchlistCard} bordered={false}>
              {etfWatchlist.length > 0 ? (
                <Table columns={etfWatchlistColumns} dataSource={etfWatchlist} rowKey="code" pagination={false} loading={etfWatchlistLoading} className={styles.fundTable} />
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无自选ETF">
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setEtfSearchModalVisible(true)}>添加ETF</Button>
                </Empty>
              )}
            </Card>
          </div>
        </>
      )}

      {/* ==================== 场外基金 Tab ==================== */}
      {activeTab === 'otc' && (
        <>
          <div className={styles.rankingSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>基金排行榜</h2>
              <Space>
                <Segmented options={OTC_FUND_TYPES.map(t => ({ label: t, value: t }))} value={otcFundType} onChange={(value) => setOtcFundType(value as string)} className={styles.fundTypeSelect} />
                <Segmented options={SORT_OPTIONS} value={otcSortBy} onChange={(value) => setOtcSortBy(value as string)} className={styles.sortSelect} />
                <Button icon={<ReloadOutlined />} loading={otcRankingLoading} onClick={() => fetchOtcRanking()}>刷新</Button>
              </Space>
            </div>

            <Card className={styles.rankingCard} bordered={false}>
              <Table columns={otcRankingColumns} dataSource={otcRanking} rowKey="code" pagination={false} loading={otcRankingLoading} className={styles.fundTable} scroll={{ y: 400 }} />
            </Card>
          </div>

          <div className={styles.watchlistSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>自选基金<span className={styles.fundCount}>({otcWatchlist.length})</span></h2>
              <Space>
                <Button icon={<ReloadOutlined />} loading={otcWatchlistLoading} onClick={() => fetchOtcWatchlist(true)}>刷新</Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setOtcSearchModalVisible(true)}>添加基金</Button>
              </Space>
            </div>

            <Card className={styles.watchlistCard} bordered={false}>
              {otcWatchlist.length > 0 ? (
                <Table columns={otcWatchlistColumns} dataSource={otcWatchlist} rowKey="code" pagination={false} loading={otcWatchlistLoading} className={styles.fundTable} />
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无自选基金">
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setOtcSearchModalVisible(true)}>添加基金</Button>
                </Empty>
              )}
            </Card>
          </div>
        </>
      )}

      {/* ==================== ETF 搜索弹窗 ==================== */}
      <Modal title="搜索ETF" open={etfSearchModalVisible} onCancel={() => { setEtfSearchModalVisible(false); setEtfSearchKeyword(''); setEtfSearchResults([]); }} footer={null} className={styles.searchModal} width={600}>
        <Input.Search placeholder="输入ETF代码或名称" allowClear enterButton={<SearchOutlined />} value={etfSearchKeyword} onChange={(e) => setEtfSearchKeyword(e.target.value)} onSearch={handleEtfSearch} loading={etfSearchLoading} className={styles.searchInput} />
        <div className={styles.searchResults}>
          {etfSearchResults.length > 0 ? (
            <List
              dataSource={etfSearchResults}
              renderItem={(item: ETFData) => (
                <List.Item className={styles.searchResultItem} actions={[<Button key="add" type="primary" size="small" onClick={() => handleAddEtfToWatchlist(item)}>添加</Button>]}>
                  <List.Item.Meta
                    title={<span>{item.name}<Tag color={etfTypeColors[item.etf_type] || 'default'} style={{ marginLeft: 8 }}>{item.etf_type}</Tag></span>}
                    description={`代码: ${item.code} | 最新价: ${item.price?.toFixed(4) || '-'} | 涨跌幅: ${formatChange(item.change_percent || 0)}`}
                  />
                </List.Item>
              )}
            />
          ) : etfSearchKeyword ? <Empty description="未找到相关ETF" /> : <Empty description="请输入关键词搜索" />}
        </div>
      </Modal>

      {/* ==================== 场外基金搜索弹窗 ==================== */}
      <Modal title="搜索基金" open={otcSearchModalVisible} onCancel={() => { setOtcSearchModalVisible(false); setOtcSearchKeyword(''); setOtcSearchResults([]); }} footer={null} className={styles.searchModal} width={600}>
        <Input.Search placeholder="输入基金代码或名称" allowClear enterButton={<SearchOutlined />} value={otcSearchKeyword} onChange={(e) => setOtcSearchKeyword(e.target.value)} onSearch={handleOtcSearch} loading={otcSearchLoading} className={styles.searchInput} />
        <div className={styles.searchResults}>
          {otcSearchResults.length > 0 ? (
            <List
              dataSource={otcSearchResults}
              renderItem={(item: OTCFundData) => (
                <List.Item className={styles.searchResultItem} actions={[<Button key="add" type="primary" size="small" onClick={() => handleAddOtcToWatchlist(item)}>添加</Button>]}>
                  <List.Item.Meta
                    title={<span>{item.name}<Tag color={fundTypeColors[item.fund_type] || 'default'} style={{ marginLeft: 8 }}>{item.fund_type}</Tag></span>}
                    description={`代码: ${item.code} | 净值: ${item.nav?.toFixed(4) || '-'} | 近1年: ${formatChange(item.return_1y || 0)}`}
                  />
                </List.Item>
              )}
            />
          ) : otcSearchKeyword ? <Empty description="未找到相关基金" /> : <Empty description="请输入关键词搜索" />}
        </div>
      </Modal>

      {/* ==================== 基金详情弹窗 ==================== */}
      <Modal title="基金详情" open={detailModalVisible} onCancel={() => { setDetailModalVisible(false); setFundDetail(null); }} footer={null} className={styles.detailModal} width={700}>
        {detailLoading ? (
          <div className={styles.detailLoading}><Spin size="large" /></div>
        ) : fundDetail ? (
          <div className={styles.detailContent}>
            <div className={styles.detailHeader}>
              <h3>{fundDetail.name}</h3>
              <Tag color={fundTypeColors[fundDetail.fund_type] || 'default'}>{fundDetail.fund_type}</Tag>
            </div>
            
            <div className={styles.detailNav}>
              <div className={styles.navItem}>
                <span className={styles.navLabel}>最新净值</span>
                <span className={`${styles.navValue} ${getChangeClass(fundDetail.change_percent)}`}>{fundDetail.nav?.toFixed(4) || '-'}</span>
              </div>
              <div className={styles.navItem}>
                <span className={styles.navLabel}>日涨跌</span>
                <span className={`${styles.navValue} ${getChangeClass(fundDetail.change_percent)}`}>{formatChange(fundDetail.change_percent || 0)}</span>
              </div>
              <div className={styles.navItem}>
                <span className={styles.navLabel}>近1年</span>
                <span className={`${styles.navValue} ${getChangeClass(fundDetail.return_1y)}`}>{formatChange(fundDetail.return_1y || 0)}</span>
              </div>
            </div>

            <Descriptions column={2} bordered size="small" className={styles.detailInfo}>
              <Descriptions.Item label="基金代码">{fundDetail.code}</Descriptions.Item>
              <Descriptions.Item label="成立时间">{fundDetail.establish_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="基金经理">{fundDetail.manager || '-'}</Descriptions.Item>
              <Descriptions.Item label="最新规模">{fundDetail.asset_size || '-'}</Descriptions.Item>
              <Descriptions.Item label="基金公司" span={2}>{fundDetail.company || '-'}</Descriptions.Item>
              <Descriptions.Item label="托管银行" span={2}>{fundDetail.custodian || '-'}</Descriptions.Item>
              <Descriptions.Item label="投资目标" span={2}>{fundDetail.investment_target || '-'}</Descriptions.Item>
            </Descriptions>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

export default Fund;
