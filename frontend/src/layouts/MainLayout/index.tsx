import React from 'react';
import { Outlet, useLocation, history } from 'umi';
import {
  DashboardOutlined,
  StockOutlined,
  FundOutlined,
  GoldOutlined,
  LineChartOutlined,
  BankOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import styles from './index.less';

interface NavItem {
  key: string;
  path: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { key: 'dashboard', path: '/dashboard', icon: <DashboardOutlined />, label: '综合' },
  { key: 'stock', path: '/stock', icon: <StockOutlined />, label: '股票' },
  { key: 'fund', path: '/fund', icon: <FundOutlined />, label: '基金' },
  { key: 'gold', path: '/gold', icon: <GoldOutlined />, label: '黄金' },
  { key: 'futures', path: '/futures', icon: <LineChartOutlined />, label: '期货' },
  { key: 'bond', path: '/bond', icon: <BankOutlined />, label: '债券' },
  { key: 'forex', path: '/forex', icon: <DollarOutlined />, label: '外汇' },
];

const MainLayout: React.FC = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  const handleNavClick = (path: string) => {
    history.push(path);
  };

  return (
    <div className={styles.layout}>
      {/* 顶部导航栏 */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          {/* Logo */}
          <div className={styles.logo}>
            <span className={styles.logoIcon}>📈</span>
            <span className={styles.logoText}>投资助理</span>
          </div>

          {/* 导航标签 */}
          <nav className={styles.nav}>
            {navItems.map((item) => (
              <div
                key={item.key}
                className={`${styles.navItem} ${
                  currentPath === item.path ? styles.navItemActive : ''
                }`}
                onClick={() => handleNavClick(item.path)}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
              </div>
            ))}
          </nav>

          {/* 右侧区域 - 预留 */}
          <div className={styles.headerRight}>
            <div className={styles.marketStatus}>
              <span className={styles.statusDot} />
              <span>交易中</span>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
