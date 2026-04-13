import React, { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Alert,
  Button,
  Card,
  Collapse,
  Descriptions,
  Empty,
  List,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import useApp from "antd/es/app/useApp";

import { AnalysisTaskDetail } from "../../types";
import { downloadPdfReport, getAnalysisTaskDetail } from "../../services/api";
import { SqlViewer, MultiSqlViewer } from "../../components/SqlViewer";
import "./AnalysisReportDetail.css";

const { Paragraph, Text, Title } = Typography;

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: "处理中", color: "processing" },
  completed: { label: "已完成", color: "success" },
  failed: { label: "失败", color: "error" },
};

const RISK_TAG_MAP: Record<number, { label: string; color: string }> = {
  1: { label: "低", color: "success" },
  2: { label: "中", color: "warning" },
  3: { label: "高", color: "error" },
};

const REMOTE_PROVIDER = "remote_workflow";

const getRiskTagClassName = (riskLevel: number): string => {
  const modifier =
    riskLevel === 1 ? "low" : riskLevel === 2 ? "medium" : riskLevel === 3 ? "high" : "default";
  return `app-risk-tag app-risk-tag--${modifier}`;
};

const getRiskTagClassNameByText = (riskText: string): string => {
  if (riskText.includes("高")) {
    return "app-risk-tag app-risk-tag--high";
  }
  if (riskText.includes("中")) {
    return "app-risk-tag app-risk-tag--medium";
  }
  if (riskText.includes("低")) {
    return "app-risk-tag app-risk-tag--low";
  }
  return "app-risk-tag app-risk-tag--default";
};

type ParsedRiskLevel = {
  label: string;
  checked: boolean;
  description: string;
};

type ParsedDetailEntry = {
  title: string;
  sql?: string;
  riskLevel?: string;
  summaryBullets: string[];
  analysisPoints: string[];
};

type ParsedDetailGroup = {
  title: string;
  emptyMessage?: string;
  entries: ParsedDetailEntry[];
};

type ParsedTable = {
  headers: string[];
  rows: string[][];
};

type OverviewMetrics = {
  totalSqlCount?: string;
  highRiskCount?: string;
  mediumRiskCount?: string;
  lowRiskCount?: string;
  noRiskCount?: string;
  mediumHighRatio?: string;
};

type ParsedRemoteReport = {
  title?: string;
  overviewParagraphs: string[];
  overviewMetrics?: OverviewMetrics;
  riskLevels: ParsedRiskLevel[];
  detailGroups: ParsedDetailGroup[];
  recommendationTable?: ParsedTable;
};

const stripMarkdown = (value: string): string =>
  value.replace(/\*\*/g, "").replace(/`/g, "").replace(/^\*\s*|\s*\*$/g, "").trim();

const renderInlineText = (text: string): ReactNode[] => {
  const normalized = text.replace(/^\*\s*|\s*\*$/g, "");
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  const parts = normalized.split(regex).filter(Boolean);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={`${part}-${index}`} className="analysis-detail-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>;
  });
};

const collectOverviewMetrics = (text: string): OverviewMetrics => {
  const metricPatterns: Array<[keyof OverviewMetrics, RegExp]> = [
    ["totalSqlCount", /共包含\s*\*\*(\d+)\*\*\s*条语句/],
    ["highRiskCount", /高风险 SQL 语句有\s*(\d+)\s*条/],
    ["mediumRiskCount", /中风险 SQL 语句有\s*(\d+)\s*条/],
    ["lowRiskCount", /低风险 SQL 语句有\s*(\d+)\s*条/],
    ["noRiskCount", /无风险 SQL 语句有\s*(\d+)\s*条/],
    ["mediumHighRatio", /中高风险语句占比\s*\*\*([\d.]+%)\*\*/],
  ];

  return metricPatterns.reduce<OverviewMetrics>((acc, [key, pattern]) => {
    const match = text.match(pattern);
    if (match?.[1]) {
      acc[key] = match[1];
    }
    return acc;
  }, {});
};

const parseRiskLevels = (lines: string[]): ParsedRiskLevel[] =>
  lines
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => {
      const content = line.replace(/^- /, "");
      const levelMatch = content.match(/^(.+?)\s+[■□]\s+\((.+)\)$/);
      if (!levelMatch) {
        return {
          label: stripMarkdown(content),
          checked: false,
          description: "",
        };
      }
      return {
        label: stripMarkdown(levelMatch[1]),
        checked: content.includes("■"),
        description: stripMarkdown(levelMatch[2]),
      };
    });

const parseMarkdownTable = (lines: string[]): ParsedTable | undefined => {
  const tableLines = lines
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|") && line.endsWith("|"));

  if (tableLines.length < 3) {
    return undefined;
  }

  const rows = tableLines.map((line) =>
    line
      .slice(1, -1)
      .split("|")
      .map((cell) => stripMarkdown(cell))
  );

  const [headers, , ...dataRows] = rows;
  return {
    headers,
    rows: dataRows,
  };
};

const parseDetailEntries = (lines: string[]): ParsedDetailEntry[] => {
  const entries: ParsedDetailEntry[] = [];
  let current: ParsedDetailEntry | null = null;

  const ensureCurrent = () => {
    if (!current) {
      current = {
        title: "分析项",
        summaryBullets: [],
        analysisPoints: [],
      };
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      continue;
    }

    if (trimmed.startsWith("#### ")) {
      if (current) {
        entries.push(current);
      }
      current = {
        title: stripMarkdown(trimmed.replace(/^####\s+/, "")),
        summaryBullets: [],
        analysisPoints: [],
      };
      continue;
    }

    ensureCurrent();
    if (!current) {
      continue;
    }

    if (trimmed.startsWith("- ")) {
      const bullet = stripMarkdown(trimmed.replace(/^- /, ""));
      if (bullet.startsWith("原始 SQL：")) {
        current.sql = bullet.replace(/^原始 SQL：/, "").trim();
      } else if (bullet.startsWith("风险等级：")) {
        current.riskLevel = bullet.replace(/^风险等级：/, "").trim();
      } else if (!bullet.startsWith("分析结果：")) {
        current.summaryBullets.push(bullet);
      }
      continue;
    }

    if (/^\d+\./.test(trimmed)) {
      const pointLines = [trimmed.replace(/^\d+\.\s*/, "").trim()];
      while (index + 1 < lines.length) {
        const nextLine = lines[index + 1];
        const nextTrimmed = nextLine.trim();
        if (!nextTrimmed || /^\d+\./.test(nextTrimmed) || nextTrimmed.startsWith("#### ")) {
          break;
        }
        pointLines.push(nextTrimmed);
        index += 1;
      }
      current.analysisPoints.push(stripMarkdown(pointLines.join(" ")));
      continue;
    }

    current.summaryBullets.push(stripMarkdown(trimmed));
  }

  if (current) {
    entries.push(current);
  }

  return entries;
};

const parseDetailGroups = (lines: string[]): ParsedDetailGroup[] => {
  const groups: ParsedDetailGroup[] = [];
  let currentTitle = "";
  let buffer: string[] = [];

  const flush = () => {
    if (!currentTitle) {
      return;
    }
    const cleaned = buffer.map((line) => line.trim()).filter(Boolean);
    const emptyLine = cleaned.find((line) => /^\*（.*）\*$/.test(line));
    groups.push({
      title: stripMarkdown(currentTitle),
      emptyMessage: emptyLine ? stripMarkdown(emptyLine) : undefined,
      entries: emptyLine ? [] : parseDetailEntries(cleaned),
    });
  };

  lines.forEach((line) => {
    if (line.trim().startsWith("### ")) {
      flush();
      currentTitle = line.trim().replace(/^###\s+/, "");
      buffer = [];
    } else {
      buffer.push(line);
    }
  });

  flush();
  return groups;
};

const parseRemoteReport = (text: string): ParsedRemoteReport | null => {
  const normalizedLines = text.replace(/\r\n/g, "\n").split("\n");
  const title = normalizedLines.find((line) => line.trim().startsWith("# "));

  const sectionMap = new Map<string, string[]>();
  let currentSection = "";
  let buffer: string[] = [];

  const flush = () => {
    if (currentSection) {
      sectionMap.set(currentSection, [...buffer]);
    }
  };

  normalizedLines.forEach((line) => {
    if (line.trim().startsWith("## ")) {
      flush();
      currentSection = stripMarkdown(line.trim().replace(/^##\s+/, ""));
      buffer = [];
      return;
    }
    if (currentSection) {
      buffer.push(line);
    }
  });
  flush();

  if (sectionMap.size === 0) {
    return null;
  }

  const overviewLines = sectionMap.get("一、分析概述") ?? [];
  const overviewParagraphs = overviewLines
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => stripMarkdown(line));
  const overviewText = overviewLines.join(" ");

  return {
    title: title ? stripMarkdown(title.replace(/^#\s+/, "")) : undefined,
    overviewParagraphs,
    overviewMetrics: collectOverviewMetrics(overviewText),
    riskLevels: parseRiskLevels(sectionMap.get("二、整体风险评估等级") ?? []),
    detailGroups: parseDetailGroups(sectionMap.get("三、分析结果详情") ?? []),
    recommendationTable: parseMarkdownTable(sectionMap.get("四、共性问题和优化建议") ?? []),
  };
};

const renderDetailEntryContent = (entry: ParsedDetailEntry): ReactNode => (
  <div className="analysis-detail-entry-body">
    {entry.sql && (
      <div className="analysis-detail-entry-card__sql">
        <SqlViewer sql={entry.sql} maxLength={80} placement="right" />
      </div>
    )}
    {entry.summaryBullets.length > 0 && (
      <ul className="analysis-detail-summary-list">
        {entry.summaryBullets.map((bullet) => (
          <li key={bullet}>{renderInlineText(bullet)}</li>
        ))}
      </ul>
    )}
    {entry.analysisPoints.length > 0 && (
      <ol className="analysis-detail-point-list">
        {entry.analysisPoints.map((point) => (
          <li key={point}>{renderInlineText(point)}</li>
        ))}
      </ol>
    )}
  </div>
);

export const AnalysisReportDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { taskId } = useParams();
  const { message } = useApp();

  const [detail, setDetail] = useState<AnalysisTaskDetail | null>(null);
  const [loading, setLoading] = useState(false);

  const loadDetail = useCallback(
    async (silent: boolean = false) => {
      if (!taskId) {
        return;
      }
      if (!silent) {
        setLoading(true);
      }
      try {
        const nextDetail = await getAnalysisTaskDetail(taskId);
        setDetail(nextDetail);
      } catch (error) {
        console.error("加载分析报告详情失败:", error);
        if (!silent) {
          message.error("加载分析报告详情失败");
        }
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [message, taskId]
  );

  useEffect(() => {
    document.title = taskId
      ? `分析详情 - ${taskId} - 慢SQL分析系统`
      : "分析详情 - 慢SQL分析系统";
  }, [taskId]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  useEffect(() => {
    if (!detail || detail.status !== "pending") {
      return;
    }
    const timer = window.setInterval(() => {
      loadDetail(true);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [detail, loadDetail]);

  const analysisResult = detail?.analysis_result ?? null;
  const isRemoteResult = analysisResult?.provider === REMOTE_PROVIDER;
  const reportUrl = detail?.report_url || analysisResult?.report_url || null;

  const remoteReportText = useMemo(() => {
    const reportContent = analysisResult?.report_content?.trim();
    if (reportContent) {
      return reportContent;
    }

    const fallbackMessages = (analysisResult?.messages ?? [])
      .map((entry) => entry.trim())
      .filter(
        (entry) =>
          Boolean(entry) &&
          entry !== analysisResult?.summary &&
          !entry.startsWith("http") &&
          !entry.includes("下载链接")
      );

    return fallbackMessages.join("\n\n").trim();
  }, [analysisResult]);

  const parsedReport = useMemo(() => parseRemoteReport(remoteReportText), [remoteReportText]);

  // 收集SQL：优先从detail.sql_text获取，如果没有则从报告中提取
  const collectSqlsFromReport = (parsedReport: ParsedRemoteReport | null): string[] => {
    if (!parsedReport) return [];
    const sqls: string[] = [];
    parsedReport.detailGroups?.forEach(group => {
      group.entries?.forEach(entry => {
        if (entry.sql) {
          console.log('Found SQL in entry:', entry.sql.substring(0, 50));
          sqls.push(entry.sql);
        }
      });
    });
    console.log('Total collected SQLs:', sqls.length);
    return sqls;
  };

  const sqlStatements = useMemo(() =>
    ((detail?.sql_text && detail.sql_text.length > 0)
      ? detail.sql_text
      : collectSqlsFromReport(parsedReport)).filter(sql => sql && sql.trim() !== ""),
    [detail?.sql_text, parsedReport]
  );

  const metadataSummary = analysisResult?.metadata_summary ?? null;
  const inputDiagnostics = analysisResult?.input_diagnostics ?? null;
  const consistencyFlags = analysisResult?.consistency_flags ?? null;
  const metadataIsIncomplete = Boolean(
    metadataSummary &&
      (
        metadataSummary.missing_tables_count > 0 ||
        metadataSummary.fetch_errors_count > 0 ||
        metadataSummary.tables_with_ddl_count < metadataSummary.matched_tables_count ||
        metadataSummary.tables_with_indexes_count < metadataSummary.matched_tables_count
      )
  );
  const metadataHasRemoteMismatch = Boolean(
    consistencyFlags &&
      Object.values(consistencyFlags).some((flag) => Boolean(flag))
  );

  const recommendationColumns = useMemo<ColumnsType<Record<string, string>>>(() => {
    if (!parsedReport?.recommendationTable) {
      return [];
    }
    return parsedReport.recommendationTable.headers.map((header, index) => ({
      title: header,
      dataIndex: `col-${index}`,
      key: `col-${index}`,
    }));
  }, [parsedReport]);

  const recommendationData = useMemo(() => {
    if (!parsedReport?.recommendationTable) {
      return [];
    }
    return parsedReport.recommendationTable.rows.map((row, rowIndex) =>
      row.reduce<Record<string, string>>(
        (acc, cell, cellIndex) => {
          acc[`col-${cellIndex}`] = cell;
          return acc;
        },
        { key: String(rowIndex) }
      )
    );
  }, [parsedReport]);

  const detailGroupItems = useMemo(
    () =>
      (parsedReport?.detailGroups ?? []).map((group, groupIndex) => ({
        key: `${group.title}-${groupIndex}`,
        label: (
          <div className="analysis-detail-group-label">
            <span className="analysis-detail-group-label__title">{group.title}</span>
            <span className="analysis-detail-group-label__meta">
              {group.entries.length > 0 ? `${group.entries.length} 项` : "无明细"}
            </span>
          </div>
        ),
        children: group.emptyMessage ? (
          <Alert type="info" showIcon message={group.emptyMessage} />
        ) : (
          <Collapse
            className="analysis-detail-entry-collapse"
            ghost
            items={group.entries.map((entry, entryIndex) => ({
              key: `${group.title}-${entry.title}-${entryIndex}`,
              label: (
                <div className="analysis-detail-entry-trigger">
                  <div>
                    <h4>{entry.title}</h4>
                    {entry.sql && <span>展开查看 SQL 与分析结论</span>}
                  </div>
                  {entry.riskLevel && (
                    <Tag className={getRiskTagClassNameByText(entry.riskLevel)}>{entry.riskLevel}</Tag>
                  )}
                </div>
              ),
              children: renderDetailEntryContent(entry),
            }))}
          />
        ),
      })),
    [parsedReport]
  );

  const handleDownload = useCallback(async () => {
    if (!reportUrl || !detail?.task_id) {
      message.warning("报告暂不可下载");
      return;
    }
    try {
      await downloadPdfReport(reportUrl, detail.task_id);
      message.success("PDF 报告下载中...");
    } catch (error) {
      console.error("下载报告失败:", error);
      message.error(error instanceof Error ? error.message : "下载报告失败");
    }
  }, [detail?.task_id, message, reportUrl]);

  if (!taskId) {
    return <Empty description="缺少任务ID" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  return (
    <div className="analysis-detail-page page-shell">
      <div className="page-banner">
        <span className="page-banner__eyebrow">Remote Analysis Detail</span>
        <Space
          style={{ width: "100%", justifyContent: "space-between" }}
          align="start"
          wrap
        >
          <div>
            <Title level={2} className="page-banner__title">
              分析详情
            </Title>
            <p className="page-banner__desc">
              当前详情页会把远端 Workflow 返回的报告拆成结构化预览，优先展示概述、风险等级、分项分析和优化建议。
            </p>
            <div className="page-banner__meta">
              <span className="page-banner__pill">任务ID：{taskId}</span>
              {detail && (
                <span className="page-banner__pill">
                  状态：{(STATUS_MAP[detail.status] || STATUS_MAP.pending).label}
                </span>
              )}
            </div>
          </div>
          <Space wrap>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/analysis/list")}>
              返回列表
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => loadDetail()}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              disabled={!reportUrl}
            >
              下载 PDF
            </Button>
          </Space>
        </Space>
      </div>

      <Spin spinning={loading && !detail}>
        {detail ? (
          <div className="analysis-detail-grid">
            <div className="analysis-detail-main">
              <Card className="analysis-detail-card surface-card">
                <Descriptions column={{ xs: 1, sm: 2, md: 5 }} bordered size="small">
                  <Descriptions.Item label="任务状态">
                    <Tag color={(STATUS_MAP[detail.status] || STATUS_MAP.pending).color}>
                      {(STATUS_MAP[detail.status] || STATUS_MAP.pending).label}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="风险等级">
                    <Tag className={getRiskTagClassName(detail.risk_level)}>
                      {(RISK_TAG_MAP[detail.risk_level] || RISK_TAG_MAP[1]).label}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="结果来源">
                    {isRemoteResult ? "远端 Workflow" : "远端结果暂不可用"}
                  </Descriptions.Item>
                  <Descriptions.Item label="数据源">
                    {detail.data_source_name || "兼容模式"}
                  </Descriptions.Item>
                  <Descriptions.Item label="目标库">
                    {detail.target_host
                      ? `${detail.target_db_type || "mysql"}://${detail.target_host}:${detail.target_port}/${detail.target_db_name}`
                      : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="创建时间">
                    {detail.created_at ? new Date(detail.created_at).toLocaleString("zh-CN") : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="完成时间">
                    {detail.finished_at ? new Date(detail.finished_at).toLocaleString("zh-CN") : "-"}
                  </Descriptions.Item>
                </Descriptions>

                {(analysisResult?.summary || detail.message) && (
                  <Alert
                    className="analysis-detail-alert"
                    type={
                      detail.status === "failed"
                        ? "error"
                        : detail.status === "pending"
                          ? "info"
                          : "success"
                    }
                    message={analysisResult?.summary || detail.message || "报告状态更新中"}
                    showIcon
                  />
                )}
              </Card>

              {isRemoteResult ? (
                remoteReportText ? (
                  <>
                    {parsedReport?.overviewMetrics && (
                      <div className="analysis-detail-metrics">
                        {parsedReport.overviewMetrics.totalSqlCount && (
                          <div className="analysis-detail-metric">
                            <span className="analysis-detail-metric__label">SQL 数量</span>
                            <span className="analysis-detail-metric__value">
                              {parsedReport.overviewMetrics.totalSqlCount}
                            </span>
                          </div>
                        )}
                        {parsedReport.overviewMetrics.mediumHighRatio && (
                          <div className="analysis-detail-metric">
                            <span className="analysis-detail-metric__label">中高风险占比</span>
                            <span className="analysis-detail-metric__value">
                              {parsedReport.overviewMetrics.mediumHighRatio}
                            </span>
                          </div>
                        )}
                        {parsedReport.overviewMetrics.lowRiskCount && (
                          <div className="analysis-detail-metric">
                            <span className="analysis-detail-metric__label">低风险条数</span>
                            <span className="analysis-detail-metric__value">
                              {parsedReport.overviewMetrics.lowRiskCount}
                            </span>
                          </div>
                        )}
                        {metadataSummary && (
                          <div className="analysis-detail-metric">
                            <span className="analysis-detail-metric__label">命中表元数据</span>
                            <span className="analysis-detail-metric__value">
                              {metadataSummary.matched_tables_count}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {parsedReport ? (
                      <>
                        <Card
                          className="analysis-detail-card analysis-detail-report surface-card"
                          title={parsedReport.title || "远端分析结果"}
                          extra={<Text type="secondary">内容与远端 PDF 同源</Text>}
                        >
                          <div className="analysis-detail-section-stack">
                            <section className="analysis-detail-section">
                              <div className="analysis-detail-section__header">
                                <h3>分析概述</h3>
                                <span>Overview</span>
                              </div>
                              <div className="analysis-detail-prose">
                                {parsedReport.overviewParagraphs.map((paragraph, index) => (
                                  <Paragraph key={`overview-${index}`} className="analysis-detail-paragraph">
                                    {renderInlineText(paragraph)}
                                  </Paragraph>
                                ))}
                              </div>
                            </section>

                            {parsedReport.riskLevels.length > 0 && (
                              <section className="analysis-detail-section">
                                <div className="analysis-detail-section__header">
                                  <h3>整体风险评估</h3>
                                  <span>Risk Score</span>
                                </div>
                                <div className="analysis-detail-risk-grid">
                                  {parsedReport.riskLevels.map((risk) => (
                                    <div
                                      key={risk.label}
                                      className={`analysis-detail-risk-card${risk.checked ? " is-active" : ""}`}
                                    >
                                      <div className="analysis-detail-risk-card__top">
                                        <Tag className={getRiskTagClassNameByText(risk.label)}>
                                          {risk.label}
                                        </Tag>
                                        <span className="analysis-detail-risk-card__flag">
                                          {risk.checked ? "当前等级" : "未命中"}
                                        </span>
                                      </div>
                                      <p>{risk.description}</p>
                                    </div>
                                  ))}
                                </div>
                              </section>
                            )}

                            {detailGroupItems.length > 0 && (
                              <section className="analysis-detail-section">
                                <div className="analysis-detail-section__header">
                                  <h3>风险详情</h3>
                                  <span>展开查看</span>
                                </div>
                                <Collapse
                                  className="analysis-detail-group-collapse"
                                  ghost
                                  items={detailGroupItems}
                                />
                              </section>
                            )}

                            {parsedReport.recommendationTable && (
                              <section className="analysis-detail-section">
                                <div className="analysis-detail-section__header">
                                  <h3>共性问题和优化建议</h3>
                                  <span>Recommendations</span>
                                </div>
                                <Table
                                  className="analysis-detail-recommendation-table"
                                  columns={recommendationColumns}
                                  dataSource={recommendationData}
                                  pagination={false}
                                  scroll={{ x: 760 }}
                                />
                              </section>
                            )}
                          </div>
                        </Card>
                      </>
                    ) : (
                      <Card
                        className="analysis-detail-card analysis-detail-report surface-card"
                        title="远端分析结果"
                        extra={<Text type="secondary">内容与远端 PDF 同源</Text>}
                      >
                        <Paragraph className="analysis-detail-report-content">
                          {remoteReportText}
                        </Paragraph>
                      </Card>
                    )}
                  </>
                ) : (
                  <Card className="analysis-detail-card surface-card">
                    <Empty
                      description={
                        detail.status === "pending"
                          ? "远端报告正在生成中，页面会自动刷新。"
                          : "远端报告正文暂未返回，请直接下载 PDF 查看。"
                      }
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  </Card>
                )
              ) : (
                <Card className="analysis-detail-card surface-card">
                  <Alert
                    type="warning"
                    showIcon
                    message="当前任务暂无可展示的远端分析结果"
                    description="请刷新当前任务状态，或重新提交远端分析任务后再查看详情。"
                  />
                </Card>
              )}
            </div>

            <div className="analysis-detail-side">
              <Card className="analysis-detail-card surface-card" title="任务信息">
                <div className="analysis-detail-meta">
                  <div className="analysis-detail-meta-item">
                    <span className="analysis-detail-meta-label">任务 ID</span>
                    <span className="analysis-detail-meta-value">{detail.task_id}</span>
                  </div>
                  <div className="analysis-detail-meta-item">
                    <span className="analysis-detail-meta-label">PDF 下载</span>
                    <span className="analysis-detail-meta-value">
                      {reportUrl ? "远端生成，本地代理下载" : "暂未生成"}
                    </span>
                  </div>
                  <div className="analysis-detail-meta-item">
                    <span className="analysis-detail-meta-label">状态消息</span>
                    <span className="analysis-detail-meta-value">
                      {analysisResult?.summary || detail.message || "-"}
                    </span>
                  </div>
                </div>
              </Card>

              {metadataSummary && (
                <Card className="analysis-detail-card surface-card" title="元数据覆盖">
                  <div className="analysis-detail-meta">
                    {metadataHasRemoteMismatch && (
                      <Alert
                        type="error"
                        showIcon
                        message="远端报告与本地权威元数据不一致"
                        description="本地已命中 DDL、索引或行数信息，但远端正文仍出现了相互冲突的描述。建议以本地元数据摘要为准复核 PDF 结论。"
                      />
                    )}
                    {metadataIsIncomplete && (
                      <Alert
                        type="warning"
                        showIcon
                        message="本次分析基于不完整元数据"
                        description="部分表未命中 DDL 或索引信息，远端报告中的索引判断可能基于缺失元数据推断，请结合真实表结构复核。"
                      />
                    )}
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">命中表数量</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.matched_tables_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">自动补拉成功</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.auto_fetched_tables_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">缺失表数量</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.missing_tables_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">补拉失败数量</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.fetch_errors_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">观测统计数量</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.sql_observation_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">含 DDL 的表</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.tables_with_ddl_count}</span>
                    </div>
                    <div className="analysis-detail-meta-item">
                      <span className="analysis-detail-meta-label">识别到索引的表</span>
                      <span className="analysis-detail-meta-value">{metadataSummary.tables_with_indexes_count}</span>
                    </div>
                    {inputDiagnostics && (
                      <div className="analysis-detail-meta-item">
                        <span className="analysis-detail-meta-label">输入长度</span>
                        <span className="analysis-detail-meta-value">{inputDiagnostics.workflow_input_length}</span>
                      </div>
                    )}
                    {inputDiagnostics && (
                      <div className="analysis-detail-meta-item">
                        <span className="analysis-detail-meta-label">压缩档位</span>
                        <span className="analysis-detail-meta-value">{inputDiagnostics.compaction_level}</span>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* 调试信息 */}
              <Card className="analysis-detail-card surface-card" title="调试信息" style={{ border: "2px solid red" }}>
                <Text code>sqlStatements.length: {sqlStatements.length}</Text>
                <br />
                <Text code>detail?.sql_text: {JSON.stringify(detail?.sql_text)}</Text>
                <br />
                <Text code>analysis_result存在: {!!detail?.analysis_result}</Text>
                <br />
                <Text code>report_content存在: {!!detail?.analysis_result?.report_content}</Text>
                <br />
                <Text code>sqlStatements内容: {sqlStatements.length > 0 ? sqlStatements[0].substring(0, 100) + "..." : "空"}</Text>
                <br />
                <Text code>parsedReport存在: {!!parsedReport}</Text>
                <br />
                <Text code>parsedReport.detailGroups数量: {parsedReport?.detailGroups?.length || 0}</Text>
              </Card>

              {sqlStatements.length > 0 && (
                <Card className="analysis-detail-card surface-card" title="SQL 查看器">
                  <Space direction="vertical" style={{ width: "100%" }} size="middle">
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      💡 悬浮预览快速查看，点击打开完整查看器（支持格式化和语法高亮）
                    </Text>
                    {sqlStatements.length === 1 ? (
                      <SqlViewer sql={sqlStatements[0]} maxLength={120} placement="left" />
                    ) : (
                      <MultiSqlViewer statements={sqlStatements} maxLength={100} placement="left" />
                    )}
                  </Space>
                </Card>
              )}

              {sqlStatements.length > 0 && (
                <Card className="analysis-detail-card surface-card" title="分析 SQL">
                  <List
                    className="analysis-detail-sql-list"
                    dataSource={sqlStatements}
                    renderItem={(sql, index) => (
                      <List.Item key={`${detail.task_id}-sql-${index}`}>
                        <div style={{ width: "100%" }}>
                          <Text strong className="analysis-detail-sql-label">
                            SQL {index + 1}
                          </Text>
                          <SqlViewer sql={sql} maxLength={100} placement="bottom" />
                        </div>
                      </List.Item>
                    )}
                  />
                </Card>
              )}
            </div>
          </div>
        ) : (
          <Empty description="未找到任务详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Spin>
    </div>
  );
};



