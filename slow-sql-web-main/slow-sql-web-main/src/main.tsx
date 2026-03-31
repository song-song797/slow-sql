import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './index.css';
import { App as AntdApp } from 'antd'; // 引入 Antd 的 App 组件

ReactDOM.createRoot(document.getElementById('root')!).render(
    <AntdApp> {/* 使用 AntdApp 包裹 */}
    <React.StrictMode>
    <ConfigProvider 
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1976d2',
          colorInfo: '#1976d2',
          colorSuccess: '#5ac86f',
          colorSuccessActive: '#42b85a',
          colorSuccessBg: '#effcf2',
          colorSuccessBgHover: '#e4f9e9',
          colorSuccessBorder: '#b7e9c2',
          colorSuccessBorderHover: '#92dca1',
          colorSuccessText: '#2f8f45',
          colorSuccessTextHover: '#287b3c',
          colorWarning: '#ffb547',
          colorWarningActive: '#f59e0b',
          colorWarningBg: '#fff8eb',
          colorWarningBgHover: '#fff1da',
          colorWarningBorder: '#ffd8a8',
          colorWarningBorderHover: '#ffc56d',
          colorWarningText: '#d98200',
          colorWarningTextHover: '#bf7400',
          colorError: '#ff7a7a',
          colorErrorActive: '#f05b5b',
          colorErrorBg: '#fff3f3',
          colorErrorBgHover: '#ffe7e7',
          colorErrorBorder: '#ffc2c2',
          colorErrorBorderHover: '#ffa0a0',
          colorErrorText: '#e14d4d',
          colorErrorTextHover: '#cb3e3e',
          colorTextBase: '#132238',
          colorTextSecondary: '#5f6f84',
          colorBorderSecondary: '#dce6f2',
          colorBgBase: '#f3f6fb',
          colorBgLayout: '#f3f6fb',
          colorBgContainer: '#ffffff',
          borderRadius: 12,
          borderRadiusLG: 20,
          borderRadiusSM: 10,
          boxShadowSecondary: '0 18px 50px rgba(15, 23, 42, 0.08)',
          fontFamily:
            '"Segoe UI Variable", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
        },
        components: {
          Layout: {
            bodyBg: '#f3f6fb',
            headerBg: 'transparent',
            headerColor: '#132238',
          },
          Button: {
            borderRadius: 999,
            controlHeight: 40,
            fontWeight: 600,
            primaryShadow: '0 12px 24px rgba(25, 118, 210, 0.18)',
          },
          Card: {
            borderRadiusLG: 22,
            boxShadowTertiary: '0 18px 50px rgba(15, 23, 42, 0.08)',
            paddingLG: 20,
          },
          Input: {
            borderRadius: 14,
            controlHeight: 42,
            activeBorderColor: '#1976d2',
            hoverBorderColor: '#64b5f6',
          },
          DatePicker: {
            borderRadius: 14,
            controlHeight: 42,
          },
          Select: {
            borderRadius: 14,
            controlHeight: 42,
          },
          Table: {
            borderColor: '#e4ebf5',
            headerBg: '#f7faff',
            headerColor: '#24415f',
            rowHoverBg: '#f5f9ff',
          },
          Tag: {
            borderRadiusSM: 999,
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
  </AntdApp>
  ,
);
