import { BrowserRouter, Routes, Route,  Link, useLocation } from 'react-router-dom';
import { Layout } from 'antd';
import { RecordSearchPage } from './pages/RecordSearch/RecordSearch';

import { AnalysisResultListPage } from './pages/AnalysisResultList/AnalysisResultList';
import { AnalysisReportDetailPage } from './pages/AnalysisReportDetail/AnalysisReportDetail';
import { DataSourceManagementPage } from './pages/DataSourceManagement/DataSourceManagement';
import './App.css';

const { Header, Content } = Layout;

// 导航菜单组件
const NavMenu = () => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="nav-menu">
      <Link to="/" className={isActive('/') ? 'active' : ''}>
        记录检索
      </Link>
      <Link to="/analysis/list" className={isActive('/analysis') ? 'active' : ''}>
        分析结果
      </Link>
      <Link to="/data-sources" className={isActive('/data-sources') ? 'active' : ''}>
        数据源管理
      </Link>
    </nav>
  );
};

// 包装组件以从路由获取参数


function App() {
  return (
    <BrowserRouter>
      <Layout className="app-layout">
        <Header className="app-header">
          <div className="header-content">
            <h1 className="logo"><a href="/">慢 SQL 分析系统</a></h1>
            <NavMenu />
          </div>
        </Header>
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<RecordSearchPage />} />
            <Route path="/analysis/list" element={<AnalysisResultListPage />} />
            <Route path="/analysis/:taskId" element={<AnalysisReportDetailPage />} />
            <Route path="/data-sources" element={<DataSourceManagementPage />} />
          </Routes>
        </Content>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
