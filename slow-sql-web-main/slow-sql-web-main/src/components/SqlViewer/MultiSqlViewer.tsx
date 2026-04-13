/**
 * 多SQL查看器组件
 * 支持查看多条SQL语句，每条SQL独立格式化和高亮
 */

import React, { useState } from "react";
import { Popover, Modal, Tabs, Button, Space, Typography, Tag, message } from "antd";
import {
  CopyOutlined,
  CheckOutlined,
  FileTextOutlined,
  CodeOutlined,
} from "@ant-design/icons";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { format } from "sql-formatter";

const { Text } = Typography;

interface MultiSqlViewerProps {
  statements: string[]; // 多条SQL语句数组
  maxLength?: number; // 表格中显示的最大长度
  placement?: "left" | "right" | "top" | "bottom"; // 悬浮预览的位置
}

export const MultiSqlViewer: React.FC<MultiSqlViewerProps> = ({
  statements,
  maxLength = 60,
  placement = "left",
}) => {
  const [previewVisible, setPreviewVisible] = useState(false);
  const [viewerVisible, setViewerVisible] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("0"); // 默认显示第一条SQL

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

  // 复制所有SQL
  const handleCopyAll = async () => {
    try {
      const allSql = statements.join("\n\n");
      await navigator.clipboard.writeText(allSql);
      setCopied(true);
      message.success("已复制所有SQL到剪贴板");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      message.error("复制失败");
    }
  };

  // 悬浮预览内容（显示前3条SQL的简预览）
  const previewContent = (
    <div style={{ maxWidth: 600 }}>
      <div style={{ marginBottom: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          💡 快速预览（点击打开完整查看器）
        </Text>
      </div>
      <div style={{ maxHeight: "250px", overflow: "auto" }}>
        {statements.slice(0, 3).map((sql, index) => (
          <div key={index} style={{ marginBottom: index < statements.slice(0, 3).length - 1 ? 12 : 0 }}>
            {statements.length > 1 && (
              <Text strong style={{ fontSize: 11, display: "block", marginBottom: 4 }}>
                SQL {index + 1}:
              </Text>
            )}
            <pre
              style={{
                margin: 0,
                padding: "8px",
                background: "#f5f5f5",
                borderRadius: "4px",
                fontSize: "10px",
                lineHeight: "1.3",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
              }}
            >
              {truncateSql(sql, 200)}
            </pre>
          </div>
        ))}
        {statements.length > 3 && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            ... 还有 {statements.length - 3} 条SQL
          </Text>
        )}
      </div>
    </div>
  );

  // 完整查看器内容
  const viewerContent = (
    <Modal
      title={
        <Space>
          <CodeOutlined />
          多SQL查看器
          <Text type="secondary" style={{ fontSize: 12, fontWeight: "normal" }}>
            ({statements.length} 条语句)
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
          <Button size="small" icon={<CopyOutlined />} onClick={handleCopyAll}>
            复制所有SQL
          </Button>
          <Button
            size="small"
            icon={copied ? <CheckOutlined /> : <CopyOutlined />}
            onClick={() => {
              const currentSql = statements[parseInt(activeTab)];
              const formattedCurrentSql = formatSql(currentSql);
              handleCopy(activeTab.includes("formatted") ? formattedCurrentSql : currentSql);
            }}
          >
            {copied ? "已复制" : "复制当前"}
          </Button>
        </Space>

        {/* 标签页 - 每条SQL一个标签 */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={statements.flatMap((sql, index) => [
            {
              key: `${index}-original`,
              label: (
                <span>
                  <FileTextOutlined />
                  SQL {index + 1} 原始
                </span>
              ),
              children: (
                <pre
                  style={{
                    padding: "16px",
                    background: "#f5f5f5",
                    borderRadius: "4px",
                    overflow: "auto",
                    maxHeight: "50vh",
                    fontSize: "12px",
                    lineHeight: "1.5",
                  }}
                >
                  {sql}
                </pre>
              ),
            },
            {
              key: `${index}-formatted`,
              label: (
                <span>
                  <CodeOutlined />
                  SQL {index + 1} 格式化
                </span>
              ),
              children: (
                <SyntaxHighlighter
                  language="sql"
                  style={oneDark}
                  customStyle={{
                    padding: "16px",
                    borderRadius: "4px",
                    maxHeight: "50vh",
                    fontSize: "12px",
                    lineHeight: "1.5",
                  }}
                  showLineNumbers
                  wrapLongLines
                >
                  {formatSql(sql)}
                </SyntaxHighlighter>
              ),
            },
          ])}
          size="small"
          tabPosition="top"
        />

        {/* 提示信息 */}
        <Text type="secondary" style={{ fontSize: 12 }}>
          💡 每条SQL都提供原始和格式化两种视图，格式化视图提供语法高亮和行号显示
        </Text>
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
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            maxWidth: "100%",
            cursor: "pointer",
          }}
          onClick={() => setViewerVisible(true)} // 点击打开完整查看器
        >
          <Text code style={{ fontSize: 12, maxWidth: 250, whiteSpace: "nowrap" }}>
            {truncateSql(statements[0], maxLength)}
          </Text>
          {statements.length > 1 && <Tag style={{ marginLeft: 8 }}>+{statements.length - 1} 条</Tag>}
        </div>
      </Popover>

      {/* 完整查看器 */}
      {viewerContent}
    </>
  );
};