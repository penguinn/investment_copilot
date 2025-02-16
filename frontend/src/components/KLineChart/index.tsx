import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import styles from './index.less';

interface KLineChartProps {
  data: any[];
}

export const KLineChart: React.FC<KLineChartProps> = ({ data = [] }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  useEffect(() => {
    if (chartRef.current) {
      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current);
      }

      // 确保数据是数组
      const chartData = Array.isArray(data) ? data : [];

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
          },
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
        },
        xAxis: {
          type: 'category',
          data: chartData.map(item => item.time || ''),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        yAxis: {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100,
          },
          {
            show: true,
            type: 'slider',
            bottom: '5%',
            start: 0,
            end: 100,
          },
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: chartData.map(item => [
              parseFloat(item.open || 0),
              parseFloat(item.close || 0),
              parseFloat(item.low || 0),
              parseFloat(item.high || 0),
            ]),
            itemStyle: {
              color: '#cf1322',
              color0: '#3f8600',
              borderColor: '#cf1322',
              borderColor0: '#3f8600',
            },
          },
        ],
      };

      chartInstance.current.setOption(option);
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, [data]);

  return <div ref={chartRef} className={styles.chart} />;
}; 