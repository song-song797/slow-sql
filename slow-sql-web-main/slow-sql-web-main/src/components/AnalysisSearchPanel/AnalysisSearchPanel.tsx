/**
 * 分析结果检索条件面板组件
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Input,
  // Select,
  Button,
  Space,
  Row,
  Col,
  Card,
  Collapse,
  Tag,
} from "antd";
import "./AnalysisSearchPanel.css";
import {
  SearchOutlined,
  ReloadOutlined,
  UpOutlined,
  DownOutlined,
  FilterOutlined,
} from "@ant-design/icons";
import { AnalysisSearchCriteria } from "../../types/analysis-search";
import dayjs, { Dayjs } from "dayjs";
import { DatePicker } from "antd";

const { RangePicker } = DatePicker;

interface AnalysisSearchPanelProps {
  criteria: AnalysisSearchCriteria;
  onSearch: (criteria: AnalysisSearchCriteria) => void;
  onReset: () => void;
}

// 快速筛选选项
const quickFilters = [
  {
    label: "今日分析",
    value: "today",
    getCriteria: () => ({
      timestamp_start: dayjs().startOf("day").format("YYYY-MM-DD HH:mm:ss"),
      timestamp_end: dayjs().endOf("day").format("YYYY-MM-DD HH:mm:ss"),
    }),
  },
  // {
  //   label: "高风险",
  //   value: "highRisk",
  //   getCriteria: () => ({
  //     riskLevel: "high" as const,
  //   }),
  // },
  {
    label: "高风险",
    value: "highRisk",
    getCriteria: () => ({
      riskLevel: "high" as const,
    }),
  },
];

export const AnalysisSearchPanel: React.FC<AnalysisSearchPanelProps> = ({
  criteria,
  onSearch,
  onReset,
}) => {
  const [localCriteria, setLocalCriteria] =
    useState<AnalysisSearchCriteria>(criteria);
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeQuickFilter, setActiveQuickFilter] = useState<string | null>(
    null
  );

  // 同步外部 criteria 变化
  useEffect(() => {
    setLocalCriteria(criteria);
  }, [criteria]);

  const handleChange = (
    field: keyof AnalysisSearchCriteria,
    value: string | number | undefined
  ) => {
    setLocalCriteria((prev) => ({
      ...prev,
      [field]: value,
      page: 1, // 搜索时重置到第一页
    }));
    // 清除快速筛选状态
    if (activeQuickFilter) {
      setActiveQuickFilter(null);
    }
  };

  const handleSearch = useCallback(() => {
    onSearch(localCriteria);
  }, [localCriteria, onSearch]);

  const handleReset = () => {
    const resetCriteria: AnalysisSearchCriteria = {
      page: 1,
      pageSize: 10,
    };
    setLocalCriteria(resetCriteria);
    setActiveQuickFilter(null);
    onReset();
  };

  // 回车搜索
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  // 快速筛选
  const handleQuickFilter = (filterValue: string) => {
    const filter = quickFilters.find((f) => f.value === filterValue);
    if (!filter) return;

    const filterCriteria = filter.getCriteria();
    const newCriteria = {
      ...localCriteria,
      ...filterCriteria,
      page: 1,
    };
    setLocalCriteria(newCriteria);
    setActiveQuickFilter(filterValue);
    onSearch(newCriteria);
  };

  const handleDateRangeChange = (
    dates: [Dayjs | null, Dayjs | null] | null
  ) => {
    if (dates && dates[0] && dates[1]) {
      handleChange("timestamp_start", dates[0].format("YYYY-MM-DD HH:mm:ss"));
      handleChange("timestamp_end", dates[1].format("YYYY-MM-DD HH:mm:ss"));
    } else {
      handleChange("timestamp_start", undefined);
      handleChange("timestamp_end", undefined);
    }
  };

  const dateRangeValue: [Dayjs | null, Dayjs | null] | null =
    localCriteria.timestamp_start && localCriteria.timestamp_end
      ? [
          dayjs(localCriteria.timestamp_start),
          dayjs(localCriteria.timestamp_end),
        ]
      : null;

  return (
    <Card
      className="analysis-search-panel surface-card"
      title={
        <Space>
          <FilterOutlined />
          <span>检索条件</span>
        </Space>
      }
      extra={
        <Button
          className="analysis-search-panel__toggle"
          type="text"
          icon={isExpanded ? <UpOutlined /> : <DownOutlined />}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? "收起" : "展开"}
        </Button>
      }
      style={{ marginBottom: 16 }}
    >
      {/* 快速筛选标签 */}
      <Space wrap className="analysis-search-panel__quick-filters">
        {quickFilters.map((filter) => (
          <Tag
            key={filter.value}
            color={activeQuickFilter === filter.value ? "blue" : "default"}
            className="analysis-search-panel__tag"
            onClick={() => handleQuickFilter(filter.value)}
          >
            {filter.label}
          </Tag>
        ))}
      </Space>

      <Collapse
        activeKey={isExpanded ? ["1"] : []}
        expandIcon={() => null} //去除默认折叠图标
        items={[
          {
            key: "1",
            children: (
              <Row gutter={[16, 16]}>
                {/* <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span>关键词搜索</span>
                    <Input
                      placeholder="输入任务ID、SQL关键词等"
                      value={localCriteria.keyword || ""}
                      onChange={(e) => handleChange("keyword", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                      prefix={<SearchOutlined />}
                    />
                  </Space>
                </Col> */}

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="analysis-search-panel__label">任务ID</span>
                    <Input
                      placeholder="输入任务ID"
                      value={localCriteria.task_id || ""}
                      onChange={(e) => handleChange("task_id", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col>

                {/* <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span>记录 ID</span>
                    <Input
                      placeholder="输入 SQL 记录 ID"
                      value={localCriteria.recordId || ""}
                      onChange={(e) => handleChange("recordId", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col> */}

                {/* <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span>风险等级</span>
                    <Select
                      placeholder="选择风险等级"
                      value={localCriteria.riskLevel || undefined}
                      onChange={(value) =>
                        handleChange("riskLevel", value || "")
                      }
                      allowClear
                      style={{ width: "100%" }}
                    >
                      <Select.Option value="low">低</Select.Option>
                      <Select.Option value="medium">中</Select.Option>
                      <Select.Option value="high">高</Select.Option>
                      <Select.Option value="critical">严重</Select.Option>
                    </Select>
                  </Space>
                </Col> */}

                <Col xs={24}  sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="analysis-search-panel__label">时间范围</span>
                    <RangePicker
                      showTime
                      format="YYYY-MM-DD HH:mm:ss"
                      value={dateRangeValue}
                      onChange={handleDateRangeChange}
                      style={{ width: "100%" }}
                      placeholder={["开始时间", "结束时间"]}
                    />
                  </Space>
                </Col>

                <Col xs={24}>
                  <Space className="analysis-search-panel__actions">
                    <Button icon={<ReloadOutlined />} onClick={handleReset}>
                      重置
                    </Button>
                    <Button
                      type="primary"
                      icon={<SearchOutlined />}
                      onClick={handleSearch}
                    >
                      搜索
                    </Button>
                  </Space>
                </Col>
              </Row>
            ),
          },
        ]}
      />
    </Card>
  );
};
