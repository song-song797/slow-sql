/**
 * 记录检索页面
 * 提供强大的检索功能和结果展示
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Card, Empty, Modal, Progress, Select, Space, Spin, Typography } from "antd";
import { CloudSyncOutlined, DatabaseOutlined, RadarChartOutlined } from "@ant-design/icons";
import { SearchPanel } from "../../components/SearchPanel/SearchPanel";
import { RecordTable } from "../../components/RecordTable/RecordTable";
import { ClusteredSqlRecord, DataSource, SearchCriteria, SearchResult } from "../../types";
import {
  analyzeSlowSql,
  getDataSources,
  getAnalysisResult,
  searchClusteredSqlRecords,
} from "../../services/api";
import useApp from "antd/es/app/useApp"; // 引入 useApp
import "./RecordSearch.css";

const { Text } = Typography;

function getDefaultSearchCriteria(): SearchCriteria {
  return {
    page: 1,
    pageSize: 10,
    sortBy: "cluster_count",
    sortOrder: "desc",
  };
}

function buildSearchScope(criteria: SearchCriteria): string {
  const {
    page: _page,
    pageSize: _pageSize,
    ...scope
  } = criteria;
  return JSON.stringify(scope);
}

export const RecordSearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchCriteria, setSearchCriteria] = useState<SearchCriteria>(getDefaultSearchCriteria);
  // 获取 message API
  const { message } = useApp();
  // 设置页面标题
  useEffect(() => {
    document.title = "聚类检索 - 慢SQL分析系统";
  }, []);
  const [searchResult, setSearchResult] = useState<SearchResult<ClusteredSqlRecord>>(
    {
      items: [],
      total: 0,
      page: 1,
      pageSize: 10,
      totalPages: 0,
    }
  );
  const [loading, setLoading] = useState(false);
  const [selectedRecordMap, setSelectedRecordMap] = useState<Record<string, ClusteredSqlRecord>>({});
  const selectionScopeRef = useRef<string>(buildSearchScope(getDefaultSearchCriteria()));
  const [dataSourceModalOpen, setDataSourceModalOpen] = useState(false);
  const [matchingDataSources, setMatchingDataSources] = useState<DataSource[]>([]);
  const [selectedDataSourceId, setSelectedDataSourceId] = useState<number | null>(null);
  const [pendingAnalysisRecords, setPendingAnalysisRecords] = useState<ClusteredSqlRecord[]>([]);
  
  // 分析进度相关状态
  const [analysisProgress, setAnalysisProgress] = useState<{
    visible: boolean;
    status: string;
    taskId: string | null;
    message: string;
    progress: number;
  }>({
    visible: false,
    status: "",
    taskId: null,
    message: "正在提交分析任务...",
    progress: 0,
  });
  
  // 用于存储定时器引用，以便清理
  const pollingIntervalRef = useRef<number | null>(null);
  const initialSearchTimerRef = useRef<number | null>(null);
  const activeSearchControllerRef = useRef<AbortController | null>(null);

  type SearchBehavior = {
    notify?: boolean;
  };

  // 执行搜索
  const handleSearch = useCallback(
    async (criteria: SearchCriteria, behavior: SearchBehavior = {}) => {
      const { notify = true } = behavior;
      if (initialSearchTimerRef.current !== null) {
        clearTimeout(initialSearchTimerRef.current);
        initialSearchTimerRef.current = null;
      }
      const nextScope = buildSearchScope(criteria);
      if (selectionScopeRef.current !== nextScope) {
        setSelectedRecordMap({});
        selectionScopeRef.current = nextScope;
      }

      setLoading(true);
      setSearchCriteria(criteria);
      activeSearchControllerRef.current?.abort();
      const controller = new AbortController();
      activeSearchControllerRef.current = controller;
      try {
        const result = await searchClusteredSqlRecords(criteria, controller.signal);
        if (activeSearchControllerRef.current !== controller) {
          return;
        }
        setSearchResult(result);
        setLoading(false);

        if (notify) {
          if (result.total === 0) {
            message.info("未找到匹配的聚类");
          } else {
            message.success(`找到 ${result.total} 个聚类`);
          }
        }
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error("搜索失败:", error);
        message.error("搜索失败，请稍后重试");
        setLoading(false);
      } finally {
        if (activeSearchControllerRef.current === controller) {
          activeSearchControllerRef.current = null;
        }
      }
    },
    [message]
  );

  // 重置搜索
  const handleReset = useCallback(() => {
    const resetCriteria = getDefaultSearchCriteria();
    setSelectedRecordMap({});
    selectionScopeRef.current = buildSearchScope(resetCriteria);
    setSearchCriteria(resetCriteria);
    handleSearch(resetCriteria, { notify: false });
  }, [handleSearch]);

  // 分页变化 ，处理页数变化的函数
  const handlePageChange = useCallback(
    (page: number, pageSize: number) => {
      const newCriteria = { ...searchCriteria, page, pageSize };
      console.log("页面变化了", newCriteria);
      handleSearch(newCriteria, { notify: false });
    },
    [searchCriteria, handleSearch]
  );

  const handleSortChange = useCallback(
    (sortBy?: string, sortOrder?: "asc" | "desc") => {
      const defaultCriteria = getDefaultSearchCriteria();
      const newCriteria: SearchCriteria = {
        ...searchCriteria,
        page: 1,
        sortBy: sortBy || defaultCriteria.sortBy,
        sortOrder: sortOrder || defaultCriteria.sortOrder,
      };
      handleSearch(newCriteria, { notify: false });
    },
    [searchCriteria, handleSearch]
  );

  // 执行分析
  const buildAnalyzeParams = useCallback(
    (records: ClusteredSqlRecord[]) =>
      records.map((record) => ({
        sql: record.sample_sql,
        db_type: record.type || "mysql",
        dbname: record.dbname,
        db_ip: record.upstream_addr || "",
        db_port: (record.type || "").toLowerCase().includes("postgres") ? 5432 : 3306,
        template_sql: record.template_sql,
        observation_override: {
          cluster_count: record.cluster_count,
          min_query_time_ms: record.min_query_time_ms ?? null,
          avg_query_time_ms: record.avg_query_time_ms ?? null,
          max_query_time_ms: record.max_query_time_ms ?? null,
          latest_timestamp: record.latest_timestamp ?? null,
        },
      })),
    []
  );

  const submitAnalysis = useCallback(
    async (records: ClusteredSqlRecord[], dataSourceId?: number | null) => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }

      try {
        setAnalysisProgress({
          visible: true,
          status: "pending",
          taskId: null,
          message: "正在提交分析任务...",
          progress: 0,
        });

        const payload = buildAnalyzeParams(records);
        const result = dataSourceId
          ? await analyzeSlowSql({
              data_source_id: dataSourceId,
              items: payload,
            })
          : await analyzeSlowSql(payload);
        setSelectedRecordMap({});
        setAnalysisProgress((prev) => ({
          ...prev,
          taskId: result.task_id,
          status: result.status || "processing",
          message: dataSourceId
            ? "分析任务已提交，正在分析中..."
            : "分析任务已以兼容模式提交，正在分析中，若元数据未命中会在报告中明确标注。",
          progress: 20,
        }));

        const pollAnalysisResult = async () => {
          try {
            const analysisResult = await getAnalysisResult(result.task_id);
            const currentStatus = analysisResult.status || "processing";
            let progress = 20;
            let statusMessage = "正在分析中...";

            if (currentStatus === "pending") {
              progress = 98;
              statusMessage = "分析进行中，请稍候...";
            } else if (currentStatus === "completed") {
              progress = 100;
              statusMessage = "分析完成！";
              setAnalysisProgress((prev) => ({
                ...prev,
                status: "completed",
                message: statusMessage,
                progress: 100,
              }));

              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
              }

              setTimeout(() => {
                setAnalysisProgress((prev) => ({ ...prev, visible: false }));
                message.success(`分析完成，共分析 ${records.length} 个聚类`);
                navigate(`/analysis/list?task_id=${result.task_id}`);
              }, 1000);
              return;
            } else if (currentStatus === "failed" || currentStatus === "error") {
              progress = 0;
              statusMessage = "分析失败，请重试";

              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
              }

              setAnalysisProgress((prev) => ({
                ...prev,
                status: "failed",
                message: statusMessage,
                progress: 0,
              }));
              return;
            }

            setAnalysisProgress((prev) => ({
              ...prev,
              status: currentStatus,
              message: statusMessage,
              progress: Math.min(prev.progress + 5, progress),
            }));
          } catch (error) {
            console.error("获取分析结果失败:", error);
          }
        };

        setTimeout(() => {
          pollAnalysisResult();
          pollingIntervalRef.current = window.setInterval(pollAnalysisResult, 10000);
        }, 2000);
      } catch (error) {
        console.error("分析失败:", error);
        message.error(error instanceof Error ? error.message : "分析失败，请稍后重试");
        setAnalysisProgress((prev) => ({
          ...prev,
          visible: false,
        }));
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    },
    [buildAnalyzeParams, message, navigate]
  );

  const handleAnalyze = useCallback(
    async (records: ClusteredSqlRecord[]) => {
      if (records.length === 0) {
        message.warning("请选择要分析的聚类");
        return;
      }

      const targets = records.map((record) => ({
        db_type: ((record.type || "mysql").toLowerCase().includes("postgres") ? "postgresql" : "mysql"),
        host: record.upstream_addr || "",
        port: (record.type || "").toLowerCase().includes("postgres") ? 5432 : 3306,
        db_name: record.dbname || "",
      }));
      const uniqueTargets = Array.from(
        new Set(targets.map((target) => `${target.db_type}|${target.host}|${target.port}|${target.db_name}`))
      );

      if (uniqueTargets.length > 1) {
        message.warning("一次分析仅支持同一个数据库的数据，请拆分选择后再分析");
        return;
      }

      const target = targets[0];
      if (!target.host || !target.db_name) {
        message.warning("当前聚类缺少完整数据库定位信息，暂时无法匹配数据源");
        return;
      }

      try {
        const response = await getDataSources({
          enabled: true,
          db_type: target.db_type,
          host: target.host,
          port: target.port,
          db_name: target.db_name,
          last_test_status: "success",
        });
        const candidates = response.items || [];

        if (candidates.length === 0) {
          message.warning("未找到已启用且测试通过的数据源，将以兼容模式继续分析，表结构和索引元数据可能不完整");
          await submitAnalysis(records, null);
          return;
        }

        if (candidates.length === 1) {
          await submitAnalysis(records, candidates[0].id);
          return;
        }

        setPendingAnalysisRecords(records);
        setMatchingDataSources(candidates);
        setSelectedDataSourceId(candidates[0].id);
        setDataSourceModalOpen(true);
      } catch (error) {
        console.error("匹配数据源失败:", error);
        message.error(error instanceof Error ? error.message : "匹配数据源失败");
      }
    },
    [message, navigate, submitAnalysis]
  );

  const handleSelectionChange = useCallback(
    (selectedRowKeys: React.Key[], currentPageRecords: ClusteredSqlRecord[]) => {
      const selectedKeySet = new Set(selectedRowKeys.map((key) => String(key)));
      setSelectedRecordMap((prev) => {
        const next = { ...prev };
        currentPageRecords.forEach((record) => {
          const recordId = String(record.cluster_id);
          if (selectedKeySet.has(recordId)) {
            next[recordId] = record;
          } else {
            delete next[recordId];
          }
        });
        return next;
      });
    },
    []
  );

  const handleClearSelection = useCallback(() => {
    setSelectedRecordMap({});
  }, []);

  const handleAnalyzeSelected = useCallback(() => {
    handleAnalyze(Object.values(selectedRecordMap));
  }, [handleAnalyze, selectedRecordMap]);
  
  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      if (initialSearchTimerRef.current !== null) {
        clearTimeout(initialSearchTimerRef.current);
        initialSearchTimerRef.current = null;
      }
      activeSearchControllerRef.current?.abort();
      activeSearchControllerRef.current = null;
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  // 初始加载
  useEffect(() => {
    initialSearchTimerRef.current = window.setTimeout(() => {
      initialSearchTimerRef.current = null;
      handleSearch(getDefaultSearchCriteria(), { notify: false });
    }, 0);

    return () => {
      if (initialSearchTimerRef.current !== null) {
        clearTimeout(initialSearchTimerRef.current);
        initialSearchTimerRef.current = null;
      }
    };
  }, [handleSearch]);

  // 获取状态显示文本和颜色
  const getStatusConfig = (status: string) => {
    const configs: Record<string, { text: string; color: string }> = {
      pending: { text: "待处理", color: "#1890ff" },
      processing: { text: "分析中", color: "#1890ff" },
      running: { text: "运行中", color: "#1890ff" },
      completed: { text: "已完成", color: "#52c41a" },
      failed: { text: "失败", color: "#ff4d4f" },
      error: { text: "错误", color: "#ff4d4f" },
    };
    return configs[status] || { text: status, color: "#1890ff" };
  };

  return (
    <div className="record-search-page page-shell">
      <div className="page-banner">
        <span className="page-banner__eyebrow">
          <RadarChartOutlined />
          SQL Insight Workspace
        </span>
        <h1 className="page-banner__title">慢 SQL 聚类检索</h1>
        <p className="page-banner__desc">
          从聚类视角快速筛出高频、高耗时语句，按数据库、执行耗时和时间范围组合检索，并直接发起远端分析。
        </p>
        <div className="page-banner__meta">
          <span className="page-banner__pill">
            <DatabaseOutlined />
            当前结果 {searchResult.total} 个聚类
          </span>
          <span className="page-banner__pill">
            <CloudSyncOutlined />
            已选择 {Object.keys(selectedRecordMap).length} 条待分析
          </span>
        </div>
      </div>

      <div className="page-content">
        <SearchPanel
          criteria={searchCriteria}
          onSearch={handleSearch}
          onReset={handleReset}
        />

        <Alert
          className="record-search-metadata-tip"
          type="info"
          showIcon
          message="发起分析时，系统会优先使用所选数据源和元数据缓存补充表结构、DDL、索引与观测统计信息；若未匹配到可用数据源，则会以兼容模式继续分析并在报告中显式标注元数据缺失。"
        />

        {searchResult.truncated && (
          <Alert
            className="record-search-metadata-tip"
            type="warning"
            showIcon
            message={`当前结果基于最近 ${searchResult.scannedRecordCount || 0} 条命中记录聚类，系统已限制扫描范围以避免后端卡死；匹配总量约 ${searchResult.totalRecordCount || 0} 条。`}
          />
        )}

        <Card className="result-section surface-card">
          <Spin spinning={loading}>
            {!loading && searchResult.items.length === 0 ? (
              <Empty
                description="暂无数据"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <RecordTable
                records={searchResult.items}
                total={searchResult.total}
                totalRecordCount={searchResult.totalRecordCount}
                scannedRecordCount={searchResult.scannedRecordCount}
                truncated={searchResult.truncated}
                page={searchResult.page}
                pageSize={searchResult.pageSize}
                sortBy={searchCriteria.sortBy}
                sortOrder={searchCriteria.sortOrder}
                selectedRowKeys={Object.keys(selectedRecordMap)}
                selectedCount={Object.keys(selectedRecordMap).length}
                onPageChange={handlePageChange}
                onSortChange={handleSortChange}
                onAnalyze={handleAnalyze}
                onAnalyzeSelected={handleAnalyzeSelected}
                onSelectionChange={handleSelectionChange}
                onClearSelection={handleClearSelection}
              />
            )}
          </Spin>
        </Card>
      </div>

      {/* 分析进度弹窗 */}
      <Modal
        title="选择数据源"
        open={dataSourceModalOpen}
        onCancel={() => {
          setDataSourceModalOpen(false);
          setPendingAnalysisRecords([]);
        }}
        onOk={async () => {
          if (!selectedDataSourceId) {
            message.warning("请选择一个数据源");
            return;
          }
          setDataSourceModalOpen(false);
          await submitAnalysis(pendingAnalysisRecords, selectedDataSourceId);
          setPendingAnalysisRecords([]);
        }}
      >
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Alert
            type="info"
            showIcon
            message="当前聚类匹配到多个可用数据源，请选择本次分析要使用的目标库。"
          />
          <Select
            style={{ width: "100%" }}
            value={selectedDataSourceId ?? undefined}
            onChange={(value) => setSelectedDataSourceId(value)}
            options={matchingDataSources.map((item) => ({
              label: `${item.name} · ${item.db_type}://${item.host}:${item.port}/${item.db_name}`,
              value: item.id,
            }))}
          />
        </Space>
      </Modal>

      <Modal
        title="SQL 分析进度"
        open={analysisProgress.visible}
        closable={analysisProgress.status === "completed" || analysisProgress.status === "failed"}
        maskClosable={false}
        footer={null}
        centered
        width={500}
        className="analysis-progress-modal"
      >
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <div>
            <Text strong>任务状态：</Text>
            <Text
              style={{
                color: getStatusConfig(analysisProgress.status).color,
                marginLeft: 8,
              }}
            >
              {getStatusConfig(analysisProgress.status).text}
            </Text>
          </div>
          
          {analysisProgress.taskId && (
            <div>
              <Text strong>任务ID：</Text>
              <Text code style={{ marginLeft: 8 }}>
                {analysisProgress.taskId}
              </Text>
            </div>
          )}
          
          <div>
            <Text strong>进度信息：</Text>
            <Text style={{ marginLeft: 8 }}>{analysisProgress.message}</Text>
          </div>
          
          <Progress
            percent={analysisProgress.progress}
            status={
              analysisProgress.status === "completed"
                ? "success"
                : analysisProgress.status === "failed" || analysisProgress.status === "error"
                ? "exception"
                : "active"
            }
            strokeColor={
              analysisProgress.status === "completed"
                ? "#52c41a"
                : analysisProgress.status === "failed" || analysisProgress.status === "error"
                ? "#ff4d4f"
                : "#1890ff"
            }
          />
          
          {analysisProgress.status === "completed" && (
            <Text type="success" style={{ display: "block", textAlign: "center" }}>
              分析完成，即将跳转到结果页面...
            </Text>
          )}
          
          {analysisProgress.status === "failed" && (
            <Text type="danger" style={{ display: "block", textAlign: "center" }}>
              分析失败，请检查后重试
            </Text>
          )}
        </Space>
      </Modal>
    </div>
  );
};
