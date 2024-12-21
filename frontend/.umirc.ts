import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {
    theme: {
      'success-color': '#52c41a',
      'error-color': '#ff4d4f',
    }
  },
  access: {},
  model: {},
  initialState: {},
  request: {},
  layout: {
    title: '投资助手',
  },
  routes: [
    {
      path: '/',
      component: '@/pages/index',
    },
  ],
  npmClient: 'yarn',
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
    },
  },
}); 