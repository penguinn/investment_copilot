/**
 * API 服务模块
 */

// 基础请求封装
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  
  if (data.code !== 0) {
    throw new Error(data.message || '请求失败');
  }

  return data.data;
}

// 市场指数 API
export const marketApi = {
  // 获取股票指数数据
  getIndex: async (market: string, indexCode: string) => {
    const result = await request<any>(`/api/market/${market}/${indexCode}`);
    // 数据在 items 字段中
    return result?.items || result;
  },
  
  // 批量获取指数数据
  getIndices: async (market: string, codes: string[]) => {
    const results = await Promise.all(
      codes.map(async code => {
        try {
          const result = await request<any>(`/api/market/${market}/${code}`);
          // 数据在 items 字段中
          return result?.items || result;
        } catch (err) {
          console.error(`Failed to get ${market}/${code}:`, err);
          return null;
        }
      })
    );
    return results.filter(Boolean);
  },
};

// 黄金 API
export const goldApi = {
  // 获取黄金实时行情
  getRealtime: async () => {
    return request<any[]>('/api/gold/realtime');
  },
};

// 基金 API（场外基金）
export const fundApi = {
  // 获取各类型基金汇总统计
  getSummary: async () => {
    return request<any[]>('/api/fund/summary');
  },
  
  // 获取基金实时净值
  getRealtime: async (fundType?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (fundType) params.append('fund_type', fundType);
    if (limit) params.append('limit', String(limit));
    const query = params.toString();
    return request<any[]>(`/api/fund/realtime${query ? '?' + query : ''}`);
  },
};

// 场外基金 API
export const otcFundApi = {
  // 获取基金排行榜
  getRanking: async (fundType?: string, sortBy?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (fundType) params.append('fund_type', fundType);
    if (sortBy) params.append('sort_by', sortBy);
    if (limit) params.append('limit', String(limit));
    const query = params.toString();
    return request<any[]>(`/api/fund/otc/ranking${query ? '?' + query : ''}`);
  },

  // 获取基金详情
  getDetail: async (code: string) => {
    return request<any>(`/api/fund/otc/detail/${code}`);
  },

  // 搜索场外基金
  search: async (keyword: string) => {
    return request<any[]>(`/api/fund/otc/search?keyword=${encodeURIComponent(keyword)}`);
  },

  // 获取自选列表
  getWatchlist: async (refresh?: boolean) => {
    const params = new URLSearchParams();
    if (refresh) params.append('refresh', 'true');
    const query = params.toString();
    return request<any[]>(`/api/fund/otc/watchlist${query ? '?' + query : ''}`);
  },

  // 添加到自选
  addToWatchlist: async (code: string, name?: string, fundType?: string) => {
    return request<any>('/api/fund/otc/watchlist', {
      method: 'POST',
      body: JSON.stringify({ code, name, fund_type: fundType }),
    });
  },

  // 移除自选
  removeFromWatchlist: async (code: string) => {
    return request<any>(`/api/fund/otc/watchlist/${code}`, {
      method: 'DELETE',
    });
  },

  // 获取基金历史净值
  getHistory: async (code: string) => {
    return request<any[]>(`/api/fund/history/${code}`);
  },
};

// ETF API（场内基金）
export const etfApi = {
  // 获取 ETF 实时行情
  getRealtime: async (etfType?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (etfType) params.append('etf_type', etfType);
    if (limit) params.append('limit', String(limit));
    const query = params.toString();
    return request<any[]>(`/api/fund/etf/realtime${query ? '?' + query : ''}`);
  },

  // 获取 ETF 历史数据
  getHistory: async (code: string, days?: number) => {
    const params = new URLSearchParams();
    if (days) params.append('days', String(days));
    const query = params.toString();
    return request<any[]>(`/api/fund/etf/history/${code}${query ? '?' + query : ''}`);
  },

  // 搜索 ETF
  search: async (keyword: string) => {
    return request<any[]>(`/api/fund/etf/search?keyword=${encodeURIComponent(keyword)}`);
  },

  // 获取热门 ETF
  getHot: async () => {
    return request<any[]>('/api/fund/etf/hot');
  },

  // 获取 ETF 自选列表
  getWatchlist: async (refresh?: boolean) => {
    const params = new URLSearchParams();
    if (refresh) params.append('refresh', 'true');
    const query = params.toString();
    return request<any[]>(`/api/fund/etf/watchlist${query ? '?' + query : ''}`);
  },

  // 添加 ETF 到自选
  addToWatchlist: async (code: string, name?: string) => {
    return request<any>('/api/fund/etf/watchlist', {
      method: 'POST',
      body: JSON.stringify({ code, name }),
    });
  },

  // 移除 ETF 自选
  removeFromWatchlist: async (code: string) => {
    return request<any>(`/api/fund/etf/watchlist/${code}`, {
      method: 'DELETE',
    });
  },
};

// 期货 API
export const futuresApi = {
  // 获取期货实时行情
  getRealtime: async (category?: string) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    const query = params.toString();
    return request<any[]>(`/api/futures/realtime${query ? '?' + query : ''}`);
  },
};

// 股票 API
export const stockApi = {
  // 获取股票实时行情
  getRealtime: async (codes?: string[], limit?: number) => {
    const params = new URLSearchParams();
    if (codes && codes.length > 0) params.append('codes', codes.join(','));
    if (limit) params.append('limit', String(limit));
    const query = params.toString();
    return request<any[]>(`/api/stock/realtime${query ? '?' + query : ''}`);
  },

  // 获取股票详情
  getDetail: async (code: string) => {
    return request<any>(`/api/stock/detail/${code}`);
  },

  // 获取股票历史数据
  getHistory: async (code: string, period?: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const query = params.toString();
    return request<any[]>(`/api/stock/history/${code}${query ? '?' + query : ''}`);
  },

  // 获取指数历史数据（用于折线图）
  getIndexHistory: async (market: string, symbol: string, days?: number) => {
    const params = new URLSearchParams();
    if (days) params.append('days', String(days));
    const query = params.toString();
    return request<any[]>(`/api/market/${market}/${symbol}/history${query ? '?' + query : ''}`);
  },

  // 搜索股票
  search: async (keyword: string, market?: string) => {
    const params = new URLSearchParams();
    params.append('keyword', keyword);
    if (market) params.append('market', market);
    const query = params.toString();
    return request<any[]>(`/api/stock/search?${query}`);
  },

  // 获取自选股列表
  getWatchlist: async (market?: string, refresh?: boolean) => {
    const params = new URLSearchParams();
    if (market) params.append('market', market);
    if (refresh) params.append('refresh', 'true');
    const query = params.toString();
    return request<any[]>(`/api/stock/watchlist${query ? '?' + query : ''}`);
  },

  // 添加自选股
  addToWatchlist: async (code: string, name?: string, market?: string) => {
    return request<any>('/api/stock/watchlist', {
      method: 'POST',
      body: JSON.stringify({ code, name, market: market || 'CN' }),
    });
  },

  // 移除自选股
  removeFromWatchlist: async (code: string) => {
    return request<any>(`/api/stock/watchlist/${code}`, {
      method: 'DELETE',
    });
  },
};
