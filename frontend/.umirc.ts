import { defineConfig } from 'umi';

export default defineConfig({
  routes: [
    {
      path: '/',
      component: '@/layouts/MainLayout',
      routes: [
        { path: '/', redirect: '/dashboard' },
        { path: '/dashboard', component: '@/pages/Dashboard', title: '综合' },
        { path: '/stock', component: '@/pages/Stock', title: '股票' },
        { path: '/fund', component: '@/pages/Fund', title: '基金' },
        { path: '/gold', component: '@/pages/Gold', title: '黄金' },
        { path: '/futures', component: '@/pages/Futures', title: '期货' },
        { path: '/bond', component: '@/pages/Bond', title: '债券' },
        { path: '/forex', component: '@/pages/Forex', title: '外汇' },
      ],
    },
  ],
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
    },
  },
  plugins: ['@umijs/plugins/dist/antd'],
  antd: {},
  npmClient: 'yarn',
  theme: {
    'primary-color': '#1890ff',
  },
});
