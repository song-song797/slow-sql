/**
 * 慢 SQL 记录表格组件
 * 显示检索结果列表，支持批量操作
 */

import React from "react";
import {
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Pagination,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type {
  FilterValue,
  SortOrder,
  SorterResult,
  TablePaginationConfig,
} from "antd/es/table/interface";
import { PlayCircleOutlined } from "@ant-design/icons";
import { ClusteredSqlRecord } from "../../types";
import { SqlViewer } from "../SqlViewer";
import "./RecordTable.css";

const { Text } = Typography;

interface RecordTableProps {
  records: ClusteredSqlRecord[];
  total: number;
  totalRecordCount?: number;
  scannedRecordCount?: number;
  truncated?: boolean;
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  selectedRowKeys: React.Key[];
  selectedCount: number;
  onPageChange: (page: number, pageSize: number) => void;
  onSortChange: (sortBy?: string, sortOrder?: "asc" | "desc") => void;
  onAnalyze: (records: ClusteredSqlRecord[]) => void;
  onAnalyzeSelected: () => void;
  onSelectionChange: (selectedRowKeys: React.Key[], currentPageRecords: ClusteredSqlRecord[]) => void;
  onClearSelection: () => void;
}

//这是一个导出的组件，具体records等数据从父组件接收
export const RecordTable: React.FC<RecordTableProps> = ({
  records,
  total,
  totalRecordCount,
  scannedRecordCount,
  truncated,
  page,
  pageSize,
  sortBy,
  sortOrder,
  selectedRowKeys,
  selectedCount,
  onPageChange,
  onSortChange,
  onAnalyze,
  onAnalyzeSelected,
  onSelectionChange,
  onClearSelection,
}) => {
  const antSortOrder: SortOrder | undefined =
    sortOrder === "asc" ? "ascend" : sortOrder === "desc" ? "descend" : undefined;

  const getExecutionTimeColor = (time: number) => {
    if (time < 1000) return "success";
    if (time < 3000) return "warning";
    return "error";
  };

  // const getStatusConfig = (status: string) => {
  //   const configs = {
  //     pending: { text: "待分析", color: "default" as const },
  //     analyzing: { text: "分析中", color: "processing" as const },
  //     completed: { text: "已完成", color: "success" as const },
  //     failed: { text: "失败", color: "error" as const },
  //   };
  //   return (
  //     configs[status as keyof typeof configs] || {
  //       text: status,
  //       color: "default" as const,
  //     }
  //   );
  // };

  const renderDuration = (time?: number | null) =>
    time === null || time === undefined ? "-" : `${time}ms`;

  const renderShare = (record: ClusteredSqlRecord) => {
    const count = record.cluster_count || 0;
    const denominator = truncated ? (scannedRecordCount || 0) : (totalRecordCount || 0);
    if (!count || !denominator) {
      return "-";
    }
    return `${((count / denominator) * 100).toFixed(count / denominator >= 0.1 ? 1 : 2)}%`;
  };

  const columns: ColumnsType<ClusteredSqlRecord> = [
    {
      title: "数据库",
      dataIndex: "dbname",
      key: "dbname",
      width: 120,
      align: "center", // 添加此行，使该列的表头和内容都居中
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      width: 100,
      align: "center", // 添加此行，使该列的表头和内容都居中
    },
    {
      title: "SQL 模板预览",
      dataIndex: "template_sql",
      key: "template_sql",
      width: 280,
      align: "center", // 添加此行，使该列的表头和内容都居中
      ellipsis: true,

      render: (text: string) => (
        <SqlViewer sql={text} maxLength={60} placement="left" />
      ),
    },
    {
      title: "命中次数",
      dataIndex: "cluster_count",
      key: "cluster_count",
      width: 120,
      align: "center",
      sorter: true,
      sortOrder: sortBy === "cluster_count" ? antSortOrder : undefined,
    },
    {
      title: "占比",
      key: "share",
      width: 140,
      align: "center",
      sorter: true,
      sortOrder: sortBy === "share" ? antSortOrder : undefined,
      render: (_value, record) => renderShare(record),
    },
    {
      title: "平均时间",
      dataIndex: "avg_query_time_ms",
      key: "avg_query_time_ms",
      width: 120,
      align: "center",
      sorter: true,
      sortOrder: sortBy === "avg_query_time_ms" ? antSortOrder : undefined,
      render: (time?: number | null) =>
        time === null || time === undefined ? (
          <Text type="secondary">-</Text>
        ) : (
          <Tag color={getExecutionTimeColor(time)}>{renderDuration(time)}</Tag>
        ),
    },
    {
      title: "用户名",
      dataIndex: "dbuser",
      key: "dbuser",
      width: 120,
      align: "center",
    },
    {
      title: "数据库地址",
      dataIndex: "upstream_addr",
      key: "upstream_addr",
      width: 150,
      align: "center",
    },
    {
      title: "操作",
      key: "action",
      width: 120,
      align: "center",
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => onAnalyze([record])}
          >
            分析
          </Button>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    preserveSelectedRowKeys: true,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      onSelectionChange(newSelectedRowKeys, records);
    },
  };

  const handleTableChange = (
    _pagination: TablePaginationConfig,
    _filters: Record<string, FilterValue | null>,
    sorter: SorterResult<ClusteredSqlRecord> | SorterResult<ClusteredSqlRecord>[]
  ) => {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter;
    const nextSortBy = typeof activeSorter?.columnKey === "string" ? activeSorter.columnKey : undefined;
    const nextSortOrder =
      activeSorter?.order === "ascend" ? "asc" : activeSorter?.order === "descend" ? "desc" : undefined;

    onSortChange(nextSortBy, nextSortOrder);
  };

  return (
    <div className="record-table-shell">
      <Space className="record-table-toolbar">
        <div>
          <Text className="record-table-toolbar__title">共找到 {total} 个聚类</Text>
          <div className="record-table-toolbar__hint">
            {truncated
              ? `当前仅基于最近 ${scannedRecordCount || 0} 条记录聚类，展示以系统保护后的结果为准`
              : "支持跨页选择后批量提交远端分析"}
          </div>
        </div>
        <Space className="record-table-toolbar__actions">
          {selectedCount > 0 && (
            <span className="record-table-selection-pill">已选择 {selectedCount} 条</span>
          )}
          <Button onClick={onClearSelection} disabled={selectedCount === 0}>
            清空已选
          </Button>
          <Button
            icon={<PlayCircleOutlined />}
            onClick={onAnalyzeSelected}
            disabled={selectedCount === 0}
          >
            批量分析 ({selectedCount})
          </Button>
        </Space>
      </Space>

      <Table
        rowSelection={rowSelection}
        columns={columns}
        dataSource={records}
        rowKey="cluster_id"
        className="record-table"
        pagination={false}
        onChange={handleTableChange}
        scroll={{ x: 1260 }}
      />

      <div className="record-table-pagination">
        <Pagination
          current={page}
          pageSize={pageSize}
          total={total}
          showSizeChanger
          showQuickJumper
          showTotal={(totalItems) => `共 ${totalItems} 个聚类`}
          pageSizeOptions={["10", "20", "50", "100"]}
          onChange={(page, pageSize) => onPageChange(page, pageSize)}
          onShowSizeChange={(_current, size) => onPageChange(1, size)}
        />
      </div>
    </div>
  );
};
