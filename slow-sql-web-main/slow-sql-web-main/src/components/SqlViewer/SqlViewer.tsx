/**
 * 混合模式 SQL 查看器组件
 * 支持悬浮预览和完整查看器两种模式
 */

import React, { useState } from "react";
import { Popover, Modal, Tabs, Button, Space, Typography, message } from "antd";
import {
  CopyOutlined,
  CheckOutlined,
  FileTextOutlined,
  CodeOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { format } from "sql-formatter";

const { Text } = Typography;

interface SqlViewerProps {
  sql: string;
  maxLength?: number; // 表格中显示的最大长度
  placement?: "left" | "right" | "top" | "bottom"; // 悬浮预览的位置
}

export const SqlViewer: React.FC<SqlViewerProps> = ({
  sql,
  maxLength = 60,
  placement = "left"
}) => {
  // 调试信息
  console.log('SqlViewer received sql:', sql ? `${sql.substring(0, 50)}... (${sql.length} chars)` : 'EMPTY');

  const [previewVisible, setPreviewVisible] = useState(false);
  const [viewerVisible, setViewerVisible] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("formatted");

  // 截断SQL用于表格显示
  const truncateSql = (sqlText: string, maxLength: number) => {
    if (sqlText.length <= maxLength) return sqlText;
    return sqlText.substring(0, maxLength) + "...";
  };

  // 格式化SQL
  const formatSql = (sqlText: string) => {
    try {
      return format(sqlText, {
        language: "mysql",
        tabWidth: 2,
        keywordCase: "upper",
        indentStyle: "standard",
      });
    } catch (error) {
      console.warn("SQL格式化失败:", error);
      return sqlText;
    }
  };

  // 复制功能
  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      message.success("已复制到剪贴板");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      message.error("复制失败");
    }
  };

  const formattedSql = formatSql(sql || "");

  // 如果SQL为空，显示提示信息
  if (!sql || sql.trim() === "") {
    return (
      <Text type="secondary" style={{ fontSize: 12 }}>
        (SQL内容为空)
      </Text>
    );
  }

  // 悬浮预览内容（轻量级）
  const previewContent = (
    <div style={{ maxWidth: 600, maxHeight: 400, overflow: "auto" }}>
      <div style={{ marginBottom: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          💡 快速预览（点击打开完整查看器）
        </Text>
      </div>
      <pre
        style={{
          margin: 0,
          padding: "12px",
          background: "#f5f5f5",
          borderRadius: "4px",
          fontSize: "11px",
          lineHeight: "1.4",
          maxHeight: "250px",
          overflow: "auto",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          fontFamily: "Monaco, Menlo, 'Ubuntu Mono', monospace"
        }}
      >
        {sql.length > 1000 ? sql.substring(0, 1000) + "\n\n... (内容过长，点击查看完整内容)" : sql}
      </pre>
    </div>
  );

  // 完整查看器内容
  const viewerContent = (
    <Modal
      title={
        <Space>
          <CodeOutlined />
          SQL 查看器
          <Text type="secondary" style={{ fontSize: 12, fontWeight: "normal" }}>
            ({sql.length} 字符)
          </Text>
        </Space>
      }
      open={viewerVisible}
      onCancel={() => setViewerVisible(false)}
      width={1000}
      footer={null}
      styles={{ body: { padding: "16px" } }}
    >
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        {/* 快捷操作栏 */}
        <Space>
          <Button
            size="small"
            icon={copied ? <CheckOutlined /> : <CopyOutlined />}
            onClick={() => handleCopy(activeTab === "formatted" ? formattedSql : sql)}
          >
            {copied ? "已复制" : "复制当前"}
          </Button>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() =>
              setActiveTab(activeTab === "formatted" ? "original" : "formatted")
            }
          >
            切换到{activeTab === "formatted" ? "原始" : "格式化"}
          </Button>
        </Space>

        {/* 标签页 */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: "original",
              label: (
                <span>
                  <FileTextOutlined />
                  原始 SQL
                </span>
              ),
              children: (
                <pre
                  style={{
                    padding: "16px",
                    background: "#f5f5f5",
                    borderRadius: "4px",
                    overflow: "auto",
                    maxHeight: "60vh",
                    fontSize: "12px",
                    lineHeight: "1.5",
                  }}
                >
                  {sql}
                </pre>
              ),
            },
            {
              key: "formatted",
              label: (
                <span>
                  <CodeOutlined />
                  格式化 SQL
                </span>
              ),
              children: (
                <SyntaxHighlighter
                  language="sql"
                  style={oneDark}
                  customStyle={{
                    padding: "16px",
                    borderRadius: "4px",
                    maxHeight: "60vh",
                    fontSize: "12px",
                    lineHeight: "1.5",
                  }}
                  showLineNumbers
                  wrapLongLines
                >
                  {formattedSql}
                </SyntaxHighlighter>
              ),
            },
          ]}
          size="small"
        />

        {/* 提示信息 */}
        {activeTab === "formatted" && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 格式化SQL提供语法高亮和行号显示，便于阅读和理解SQL结构
          </Text>
        )}
      </Space>
    </Modal>
  );

  return (
    <>
      {/* 触发器：SQL文本 + 悬浮预览 */}
      <Popover
        content={previewContent}
        title={null}
        trigger="hover"
        open={previewVisible}
        onOpenChange={(visible) => setPreviewVisible(visible)}
        placement={placement}
        overlayInnerStyle={{ padding: "12px" }}
        mouseEnterDelay={0.5} // 延迟0.5秒显示，避免误触发
        mouseLeaveDelay={0.1}
      >
        <Text
          code
          style={{
            fontSize: 12,
            cursor: "pointer",
            display: "inline-block",
            maxWidth: "100%",
          }}
          onClick={() => setViewerVisible(true)} // 点击打开完整查看器
        >
          {truncateSql(sql, maxLength)}
        </Text>
      </Popover>

      {/* 完整查看器 */}
      {viewerContent}
    </>
  );
};