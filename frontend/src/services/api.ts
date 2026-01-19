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

// 基金 API
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
