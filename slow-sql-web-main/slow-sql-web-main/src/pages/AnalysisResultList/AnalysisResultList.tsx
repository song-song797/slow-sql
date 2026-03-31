import React, { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Button,
  Card,
  Empty,
  Pagination,
  Popconfirm,
  Popover,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { TableRowSelection } from "antd/es/table/interface";
import {
  DownloadOutlined,
  EyeOutlined,
  FileSearchOutlined,
  FundProjectionScreenOutlined,
  DeleteOutlined,
  SafetyOutlined,
  InboxOutlined,
} from "@ant-design/icons";

import { AnalysisSearchPanel } from "../../components/AnalysisSearchPanel/AnalysisSearchPanel";
import {
  downloadPdfReport,
  downloadPdfReportsZip,
  getAnalysisResults,
  getAnalysisTaskDetail,
  hideAnalysisTask,
  hideAnalysisTasks,
} from "../../services/api";
import { AnalysisSearchCriteria } from "../../types/analysis-search";
import { AnalysisResult } from "../../types";
import "./AnalysisResultList.css";

const { Text } = Typography;

const getRiskTagClassName = (riskLevel: number): string => {
  const modifier =
    riskLevel === 1 ? "low" : riskLevel === 2 ? "medium" : riskLevel === 3 ? "high" : "default";
  return `app-risk-tag app-risk-tag--${modifier}`;
};

export const AnalysisResultListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialTaskId = searchParams.get("task_id") || undefined;

  const [searchCriteria, setSearchCriteria] = useState<AnalysisSearchCriteria>({
    page: 1,
    pageSize: 10,
    task_id: initialTaskId,
  });
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const loadResults = useCallback(async (criteria: AnalysisSearchCriteria) => {
    setLoading(true);
    try {
      const data = await getAnalysisResults({
        task_id: criteria.task_id,
        riskLevel: criteria.riskLevel,
        start_time: criteria.timestamp_start,
        end_time: criteria.timestamp_end,
        page: criteria.page,
        pageSize: criteria.pageSize,
      });
      setResults(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error("加载分析结果失败:", error);
      message.error("加载分析结果失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    document.title = "分析结果 - 慢SQL分析系统";
  }, []);

  useEffect(() => {
    setSearchCriteria((prev) => ({
      ...prev,
      page: 1,
      task_id: initialTaskId,
    }));
  }, [initialTaskId]);

  useEffect(() => {
    loadResults(searchCriteria);
  }, [loadResults, searchCriteria]);

  const handleSearch = useCallback(
    (criteria: AnalysisSearchCriteria) => {
      setSearchCriteria(criteria);
      const nextParams = new URLSearchParams();
      if (criteria.task_id) {
        nextParams.set("task_id", criteria.task_id);
      }
      navigate(`/analysis/list${nextParams.toString() ? `?${nextParams.toString()}` : ""}`, {
        replace: true,
      });
    },
    [navigate]
  );

  const handleReset = useCallback(() => {
    navigate("/analysis/list", { replace: true });
    setSearchCriteria({
      page: 1,
      pageSize: 10,
    });
    setSelectedRowKeys([]);
  }, [navigate]);

  const handlePageChange = useCallback((page: number, pageSize: number) => {
    setSearchCriteria((prev) => ({
      ...prev,
      page,
      pageSize,
    }));
  }, []);

  const handleView = (result: AnalysisResult) => {
    navigate(`/analysis/${result.task_id}`);
  };

  const hasViewableReport = (result: AnalysisResult) =>
    Boolean(result.analysis_result?.report_content || result.analysis_result?.summary || result.report_url);

  const handleDownload = async (result: AnalysisResult) => {
    try {
      const detail = await getAnalysisTaskDetail(result.task_id);
      const reportUrl = detail.report_url || result.report_url;
      if (!reportUrl) {
        message.warning("报告暂不可用");
        return;
      }

      await downloadPdfReport(reportUrl, result.task_id);
      message.success("PDF 报告下载中...");
    } catch (error) {
      console.error("下载失败:", error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      message.error(`下载失败: ${errorMessage}`);
    }
  };

  const handleHide = useCallback(
    async (result: AnalysisResult) => {
      try {
        await hideAnalysisTask(result.task_id);
        message.success("任务已从列表中移除");

        const nextPage =
          results.length === 1 && (searchCriteria.page || 1) > 1
            ? (searchCriteria.page || 1) - 1
            : searchCriteria.page || 1;

        setSearchCriteria((prev) => ({
          ...prev,
          page: nextPage,
        }));
        setSelectedRowKeys((prev) => prev.filter((key) => key !== result.task_id));
      } catch (error) {
        console.error("移除任务失败:", error);
        message.error(error instanceof Error ? error.message : "移除任务失败");
      }
    },
    [results.length, searchCriteria.page]
  );

  const handleBatchHide = useCallback(async () => {
    const taskIds = selectedRowKeys.map(String);
    if (taskIds.length === 0) {
      message.warning("请先选择要移除的任务");
      return;
    }

    try {
      const response = await hideAnalysisTasks(taskIds);
      message.success(response.message);
      setSelectedRowKeys([]);

      const nextPage =
        results.length === taskIds.length && (searchCriteria.page || 1) > 1
          ? (searchCriteria.page || 1) - 1
          : searchCriteria.page || 1;

      setSearchCriteria((prev) => ({
        ...prev,
        page: nextPage,
      }));
    } catch (error) {
      console.error("批量移除失败:", error);
      message.error(error instanceof Error ? error.message : "批量移除失败");
    }
  }, [results.length, searchCriteria.page, selectedRowKeys]);

  const handleBatchDownload = useCallback(async () => {
    const taskIds = selectedRowKeys.map(String);
    if (taskIds.length === 0) {
      message.warning("请先选择要下载的任务");
      return;
    }

    try {
      await downloadPdfReportsZip(taskIds);
      message.success("批量报告打包下载中...");
    } catch (error) {
      console.error("批量下载失败:", error);
      message.error(error instanceof Error ? error.message : "批量下载失败");
    }
  }, [selectedRowKeys]);

  const truncateSql = (sql: string, maxLength: number = 80) => {
    if (sql.length <= maxLength) {
      return sql;
    }
    return `${sql.substring(0, maxLength)}...`;
  };

  const columns: ColumnsType<AnalysisResult> = [
    {
      title: "任务ID",
      dataIndex: "task_id",
      key: "task_id",
      width: 230,
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: "涉及的 SQL 语句",
      dataIndex: "sql_text",
      key: "sql_text",
      ellipsis: true,
      width: 300,
      render: (statements: string[] | undefined) => {
        if (!statements || statements.length === 0) {
          return <Text type="secondary">无 SQL 语句</Text>;
        }
        return (
          <Popover
            title="完整 SQL"
            content={
              <div className="analysis-result-sql-popover">
                {statements.map((sql, index) => (
                  <div key={index} className="analysis-result-sql-block">
                    {statements.length > 1 && (
                      <Text strong style={{ display: "block", marginBottom: 8 }}>
                        SQL {index + 1}:
                      </Text>
                    )}
                    <pre className="analysis-result-sql-preview">{sql}</pre>
                  </div>
                ))}
              </div>
            }
          >
            <div style={{ display: "inline-flex", alignItems: "center", maxWidth: "100%" }}>
              <Text code style={{ fontSize: 12, maxWidth: 250, whiteSpace: "nowrap" }}>
                {truncateSql(statements[0])}
              </Text>
              {statements.length > 1 && <Tag style={{ marginLeft: 8 }}>+{statements.length - 1} 条</Tag>}
            </div>
          </Popover>
        );
      },
    },
    {
      title: "数据源",
      key: "data_source_name",
      width: 220,
      render: (_, record) => {
        if (!record.data_source_name) {
          return <Text type="secondary">兼容模式</Text>;
        }
        return (
          <div>
            <Text strong>{record.data_source_name}</Text>
            <div className="analysis-result-row-subtle">
              {record.target_db_type}://{record.target_host}:{record.target_port}/{record.target_db_name}
            </div>
          </div>
        );
      },
    },
    {
      title: "风险等级",
      dataIndex: "risk_level",
      key: "risk_level",
      width: 100,
      render: (riskLevel: number) => {
        const config = {
          1: { label: "低" },
          2: { label: "中" },
          3: { label: "高" },
        }[riskLevel] || { label: "-" };
        return <Tag className={getRiskTagClassName(riskLevel)}>{config.label}</Tag>;
      },
    },
    {
      title: "元数据覆盖",
      key: "metadata_summary",
      width: 220,
      render: (_, record) => {
        const summary = record.analysis_result?.metadata_summary;
        const consistencyFlags = record.analysis_result?.consistency_flags;
        if (!summary) {
          return <Text type="secondary">暂无摘要</Text>;
        }
        const incomplete =
          summary.missing_tables_count > 0 ||
          summary.fetch_errors_count > 0 ||
          summary.tables_with_ddl_count < summary.matched_tables_count ||
          summary.tables_with_indexes_count < summary.matched_tables_count;
        const hasConsistencyMismatch = Boolean(
          consistencyFlags &&
            Object.values(consistencyFlags).some((flag) => Boolean(flag))
        );
        return (
          <div>
            <Text strong>{summary.matched_tables_count} 张表命中元数据</Text>
            <div className="analysis-result-row-subtle">
              DDL {summary.tables_with_ddl_count} / 索引 {summary.tables_with_indexes_count} / 缺失 {summary.missing_tables_count}
            </div>
            {incomplete && (
              <div className="analysis-result-row-subtle">当前报告基于不完整元数据</div>
            )}
            {hasConsistencyMismatch && (
              <div className="analysis-result-row-subtle">远端结论与本地元数据不一致</div>
            )}
          </div>
        );
      },
    },
    {
      title: "执行分析时间",
      dataIndex: "finished_at",
      key: "finished_at",
      width: 180,
      render: (_: unknown, record: AnalysisResult) => {
        const timeStr = record.finished_at || record.created_at;
        return <Text>{timeStr ? new Date(timeStr).toLocaleString("zh-CN") : "-"}</Text>;
      },
    },
    {
      title: "操作",
      key: "action",
      width: 240,
      fixed: "right",
      render: (_, record) => (
        <Space size="small" className="analysis-result-row-actions">
          {hasViewableReport(record) ? (
            <>
              <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
                查看
              </Button>
              {record.report_url ? (
                <Button
                  type="link"
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(record)}
                >
                  下载
                </Button>
              ) : (
                <Text type="secondary">仅正文</Text>
              )}
            </>
          ) : (
            <Text type="secondary">报告分析中</Text>
          )}
          <Popconfirm
            title="从列表移除这条任务？"
            description="仅从结果列表隐藏，不会删除实际任务数据。"
            okText="移除"
            cancelText="取消"
            onConfirm={() => handleHide(record)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              移除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const highRiskCount = results.filter((item) => item.risk_level === 3).length;
  const downloadableCount = results.filter((item) => Boolean(item.report_url)).length;
  const rowSelection: TableRowSelection<AnalysisResult> = {
    selectedRowKeys,
    preserveSelectedRowKeys: true,
    onChange: (nextSelectedRowKeys) => setSelectedRowKeys(nextSelectedRowKeys),
  };

  return (
    <div className="analysis-result-page page-shell">
      <div className="page-banner">
        <span className="page-banner__eyebrow">
          <FundProjectionScreenOutlined />
          Remote Workflow Reports
        </span>
        <h1 className="page-banner__title">分析结果中心</h1>
        <p className="page-banner__desc">
          聚合远端 Workflow 返回的分析任务，支持按任务 ID、时间范围和风险等级筛查，并在列表中直接查看或下载报告。
        </p>
        <div className="page-banner__meta">
          <span className="page-banner__pill">
            <FileSearchOutlined />
            当前命中 {total} 条结果
          </span>
          <span className="page-banner__pill">
            <SafetyOutlined />
            当前页高风险 {highRiskCount} 条
          </span>
        </div>
      </div>

      <div className="analysis-result-summary">
        <div className="analysis-result-metric">
          <span className="analysis-result-metric__label">结果总数</span>
          <span className="analysis-result-metric__value">{total}</span>
          <span className="analysis-result-metric__hint">按当前筛选条件返回</span>
        </div>
        <div className="analysis-result-metric">
          <span className="analysis-result-metric__label">可下载报告</span>
          <span className="analysis-result-metric__value">{downloadableCount}</span>
          <span className="analysis-result-metric__hint">当前页已生成 PDF</span>
        </div>
        <div className="analysis-result-metric">
          <span className="analysis-result-metric__label">高风险任务</span>
          <span className="analysis-result-metric__value">{highRiskCount}</span>
          <span className="analysis-result-metric__hint">风险等级为高</span>
        </div>
      </div>

      {initialTaskId && (
        <Card className="analysis-result-filter-card surface-card">
          <Space wrap>
            <Text strong>当前筛选任务ID：</Text>
            <span className="analysis-result-filter-chip">
              <Text code>{initialTaskId}</Text>
            </span>
            <Button size="small" onClick={handleReset}>
              清除筛选
            </Button>
          </Space>
        </Card>
      )}

      <AnalysisSearchPanel criteria={searchCriteria} onSearch={handleSearch} onReset={handleReset} />

      <Card className="analysis-result-table-card surface-card">
        <Spin spinning={loading}>
          {!loading && results.length === 0 ? (
            <Empty description="暂无分析结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <>
              <div className="analysis-result-toolbar">
                <div className="analysis-result-toolbar__text">
                  <Text strong>已选 {selectedRowKeys.length} 条任务</Text>
                  <Text type="secondary">支持批量移除和批量下载 ZIP 报告包</Text>
                </div>
                <Space wrap>
                  <Button
                    icon={<InboxOutlined />}
                    onClick={handleBatchDownload}
                    disabled={selectedRowKeys.length === 0}
                  >
                    批量下载 ZIP
                  </Button>
                  <Popconfirm
                    title="批量从列表移除选中任务？"
                    description="仅从结果列表隐藏，不会删除实际任务数据。"
                    okText="移除"
                    cancelText="取消"
                    onConfirm={handleBatchHide}
                    disabled={selectedRowKeys.length === 0}
                  >
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      disabled={selectedRowKeys.length === 0}
                    >
                      批量移除
                    </Button>
                  </Popconfirm>
                </Space>
              </div>
              <Table
                rowSelection={rowSelection}
                columns={columns}
                dataSource={results}
                rowKey="task_id"
                pagination={false}
                scroll={{ x: 1280 }}
              />
              <div style={{ marginTop: 16, textAlign: "right" }}>
                <Pagination
                  current={searchCriteria.page}
                  pageSize={searchCriteria.pageSize}
                  total={total}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(count) => `共 ${count} 条`}
                  pageSizeOptions={["10", "20", "50", "100"]}
                  onChange={(page, pageSize) => handlePageChange(page, pageSize)}
                  onShowSizeChange={(_current, size) => handlePageChange(1, size)}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>
    </div>
  );
};
