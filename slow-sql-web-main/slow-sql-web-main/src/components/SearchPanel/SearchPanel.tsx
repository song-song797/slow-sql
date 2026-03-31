/**
 * 检索条件面板组件
 * 提供强大的检索功能，支持多种筛选条件
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Input,
  Select,
  Button,
  Space,
  Row,
  Col,
  Card,
  Collapse,
  Tag,
} from "antd";
import {
  SearchOutlined,
  ReloadOutlined,
  UpOutlined,
  DownOutlined,
  FilterOutlined,
} from "@ant-design/icons";
import { SearchCriteria } from "../../types";
import dayjs, { Dayjs } from "dayjs";
import { DatePicker } from "antd";
import "./SearchPanel.css";

const { RangePicker } = DatePicker;

interface SearchPanelProps {
  criteria: SearchCriteria;
  onSearch: (criteria: SearchCriteria) => void;
  onReset: () => void;
}

// 快速筛选选项
const quickFilters = [
  {
    label: "今日慢 SQL",
    value: "today",
    getCriteria: () => ({
      timestamp_start: dayjs().startOf("day").format("YYYY-MM-DD HH:mm:ss"),
      timestamp_end: dayjs().endOf("day").format("YYYY-MM-DD HH:mm:ss"),
    }),
  },
  {
    label: "超过 5 秒",
    value: "over5s",
    getCriteria: () => ({
      query_time_min: 5000,
    }),
  },
  // {
  //   label: "未分析",
  //   value: "pending",
  //   getCriteria: () => ({
  //     status: "pending" as const,
  //   }),
  // },
  // {
  //   label: "高风险",
  //   value: "highRisk",
  //   getCriteria: () => ({
  //     riskLevel: "high" as const,
  //   }),
  // },
];

export const SearchPanel: React.FC<SearchPanelProps> = ({
  criteria,
  onSearch,
  onReset,
}) => {
  const [localCriteria, setLocalCriteria] = useState<SearchCriteria>(criteria);
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeQuickFilter, setActiveQuickFilter] = useState<string | null>(
    null
  );

  // 同步外部 criteria 变化
  useEffect(() => {
    setLocalCriteria(criteria);
  }, [criteria]);

  const handleChange = (
    field: keyof SearchCriteria,
    value: string | number | boolean | undefined
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
    const resetCriteria: SearchCriteria = {
      page: 1,
      pageSize: 10,
    };
    setLocalCriteria(resetCriteria);
    setActiveQuickFilter(null);
    onReset();
  };
  // 定义筛选条件的基础骨架（仅保留分页通用字段，清空所有业务筛选字段）
  const getBaseCriteria = (): Pick<SearchCriteria, "page" | "pageSize"> => {
    return {
      page: 1, // 快捷筛选默认重置到第1页
      pageSize: localCriteria.pageSize || 10, // 保留用户之前设置的页大小（可选）
    };
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
      //   ...localCriteria,
      ...getBaseCriteria(), // 仅保留基础骨架
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
      className="search-panel-card surface-card"
      title={
        <Space>
          <FilterOutlined />
          <span>检索条件</span>
        </Space>
      }
      extra={
        <Button
          className="search-panel-toggle"
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
      <Space wrap className="search-panel-quick-filters">
        {quickFilters.map((filter) => (
          <Tag
            key={filter.value}
            color={activeQuickFilter === filter.value ? "blue" : "default"}
            className="search-panel-quick-filter"
            onClick={() => handleQuickFilter(filter.value)}
          >
            {filter.label}
          </Tag>
        ))}
      </Space>

      <Collapse
        activeKey={isExpanded ? ["1"] : []}
        ghost
        expandIcon={() => null}
        items={[
          {
            key: "1",
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">关键词搜索</span>
                    <Input
                      placeholder="输入 SQL 关键词或语句片段"
                      value={localCriteria.keyword || ""}
                      onChange={(e) => handleChange("keyword", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                      prefix={<SearchOutlined />}
                    />
                  </Space>
                </Col>

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">数据库名</span>
                    <Input
                      placeholder="输入数据库名"
                      value={localCriteria.dbname || ""}
                      onChange={(e) => handleChange("dbname", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col>

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">数据库类型</span>
                    <Input
                      placeholder="输入数据库类型"
                      value={localCriteria.type || ""}
                      onChange={(e) => handleChange("type", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col>

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">执行时间 (ms)</span>
                    <Space.Compact style={{ width: "100%" }}>
                      <Input
                        type="number"
                        min={0}
                        placeholder="最小值"
                        value={localCriteria.query_time_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "query_time_min",
                            e.target.value ? Number(e.target.value) : undefined
                          )
                        }
                        onPressEnter={handleKeyPress}
                        style={{ width: "50%" }}
                      />
                      <Input
                        type="number"
                        placeholder="最大值"
                        min={0}
                        value={localCriteria.query_time_max || ""}
                        onChange={(e) =>
                          handleChange(
                            "query_time_max",
                            e.target.value ? Number(e.target.value) : undefined
                          )
                        }
                        onPressEnter={handleKeyPress}
                        style={{ width: "50%" }}
                      />
                    </Space.Compact>
                  </Space>
                </Col>

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">是否慢SQL</span>
                    <Select
                      placeholder="选择是否慢SQL"
                      value={localCriteria.is_slow_sql}
                      onChange={(value) => handleChange("is_slow_sql", value)}
                      allowClear
                      style={{ width: "100%" }}
                    >
                      <Select.Option value={true}>是</Select.Option>
                      <Select.Option value={false}>否</Select.Option>
                    </Select>
                  </Space>
                </Col>
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

                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">数据库地址</span>
                    <Input
                      placeholder="输入数据库地址"
                      value={localCriteria.upstream_addr || ""}
                      onChange={(e) =>
                        handleChange("upstream_addr", e.target.value)
                      }
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">用户名</span>
                    <Input
                      placeholder="输入用户名"
                      value={localCriteria.dbuser || ""}
                      onChange={(e) => handleChange("dbuser", e.target.value)}
                      onPressEnter={handleKeyPress}
                      allowClear
                    />
                  </Space>
                </Col>
                <Col xs={24} sm={24} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span className="search-panel-label">时间范围</span>
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
                {/* <Col xs={24} sm={12} md={8}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <span>状态</span>
                    <Select
                      placeholder="选择状态"
                      value={localCriteria.status || undefined}
                      onChange={(value) => handleChange("status", value || "")}
                      allowClear
                      style={{ width: "100%" }}
                    >
                      <Select.Option value="pending">待分析</Select.Option>
                      <Select.Option value="analyzing">分析中</Select.Option>
                      <Select.Option value="completed">已完成</Select.Option>
                      <Select.Option value="failed">失败</Select.Option>
                    </Select>
                  </Space>
                </Col> */}
                <Col xs={24}>
                  <Space className="search-panel-actions">
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
