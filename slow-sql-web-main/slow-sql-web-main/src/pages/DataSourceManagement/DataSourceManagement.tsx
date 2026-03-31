import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  CheckCircleOutlined,
  CloudSyncOutlined,
  EditOutlined,
  LinkOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons";

import { DataSource, DataSourceFormValues } from "../../types";
import {
  createDataSource,
  disableDataSource,
  enableDataSource,
  getDataSources,
  syncDataSourceMetadata,
  testDataSource,
  updateDataSource,
} from "../../services/api";
import "./DataSourceManagement.css";

const { Paragraph, Text } = Typography;

const dbTypeOptions = [
  { label: "MySQL", value: "mysql" },
  { label: "PostgreSQL", value: "postgresql" },
];

const getStatusTag = (status?: string | null) => {
  if (status === "success") {
    return <Tag color="success">已通过</Tag>;
  }
  if (status === "failed") {
    return <Tag color="error">失败</Tag>;
  }
  return <Tag>未测试</Tag>;
};

export const DataSourceManagementPage: React.FC = () => {
  const [items, setItems] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingItem, setEditingItem] = useState<DataSource | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm<DataSourceFormValues>();

  const loadDataSources = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getDataSources();
      setItems(response.items || []);
    } catch (error) {
      console.error("加载数据源失败:", error);
      message.error(error instanceof Error ? error.message : "加载数据源失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    document.title = "数据源管理 - 慢SQL分析系统";
    loadDataSources();
  }, [loadDataSources]);

  const openCreateModal = useCallback(() => {
    setEditingItem(null);
    form.setFieldsValue({
      name: "",
      db_type: "mysql",
      host: "",
      port: 3306,
      db_name: "",
      username: "",
      password: "",
      enabled: true,
    });
    setModalOpen(true);
  }, [form]);

  const openEditModal = useCallback(
    (item: DataSource) => {
      setEditingItem(item);
      form.setFieldsValue({
        name: item.name,
        db_type: item.db_type,
        host: item.host,
        port: item.port,
        db_name: item.db_name,
        username: item.username,
        password: "",
        enabled: item.enabled,
      });
      setModalOpen(true);
    },
    [form]
  );

  const handleSave = useCallback(async () => {
    try {
      const values = await form.validateFields();
      if (editingItem) {
        const payload: Partial<DataSourceFormValues> = { ...values };
        if (!payload.password) {
          delete payload.password;
        }
        await updateDataSource(editingItem.id, payload);
        message.success("数据源已更新");
      } else {
        await createDataSource(values);
        message.success("数据源已创建");
      }
      setModalOpen(false);
      await loadDataSources();
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message);
      }
    }
  }, [editingItem, form, loadDataSources]);

  const handleToggleEnabled = useCallback(async (item: DataSource, enabled: boolean) => {
    try {
      if (enabled) {
        await enableDataSource(item.id);
        message.success("数据源已启用");
      } else {
        await disableDataSource(item.id);
        message.success("数据源已停用");
      }
      await loadDataSources();
    } catch (error) {
      console.error("更新数据源状态失败:", error);
      message.error(error instanceof Error ? error.message : "更新数据源状态失败");
    }
  }, [loadDataSources]);

  const handleTest = useCallback(async (item: DataSource) => {
    try {
      const result = await testDataSource(item.id);
      message.success(result.message);
      await loadDataSources();
    } catch (error) {
      console.error("测试连接失败:", error);
      message.error(error instanceof Error ? error.message : "测试连接失败");
      await loadDataSources();
    }
  }, [loadDataSources]);

  const handleSync = useCallback(async (item: DataSource) => {
    try {
      const result = await syncDataSourceMetadata(item.id);
      message.success(`${result.message}，共同步 ${result.synced_count} 张表`);
      await loadDataSources();
    } catch (error) {
      console.error("同步元数据失败:", error);
      message.error(error instanceof Error ? error.message : "同步元数据失败");
    }
  }, [loadDataSources]);

  const columns = useMemo<ColumnsType<DataSource>>(
    () => [
      {
        title: "数据源名称",
        dataIndex: "name",
        key: "name",
        width: 180,
        render: (value: string, record) => (
          <div>
            <Text strong>{value}</Text>
            <div className="data-source-table__subtle">
              {record.db_type}://{record.host}:{record.port}/{record.db_name}
            </div>
          </div>
        ),
      },
      {
        title: "账号",
        dataIndex: "username",
        key: "username",
        width: 140,
      },
      {
        title: "启用状态",
        dataIndex: "enabled",
        key: "enabled",
        width: 120,
        render: (enabled: boolean) => (enabled ? <Tag color="success">启用中</Tag> : <Tag>已停用</Tag>),
      },
      {
        title: "连接测试",
        key: "last_test_status",
        width: 200,
        render: (_, record) => (
          <div>
            {getStatusTag(record.last_test_status)}
            <div className="data-source-table__subtle">
              {record.last_test_message || "尚未测试连接"}
            </div>
          </div>
        ),
      },
      {
        title: "最近测试时间",
        dataIndex: "last_test_at",
        key: "last_test_at",
        width: 180,
        render: (value?: string | null) => (value ? new Date(value).toLocaleString("zh-CN") : "-"),
      },
      {
        title: "操作",
        key: "actions",
        width: 320,
        render: (_, record) => (
          <Space wrap>
            <Button type="link" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
              编辑
            </Button>
            <Button type="link" icon={<CheckCircleOutlined />} onClick={() => handleTest(record)}>
              测试连接
            </Button>
            <Button type="link" icon={<CloudSyncOutlined />} onClick={() => handleSync(record)}>
              同步元数据
            </Button>
            <Popconfirm
              title={record.enabled ? "停用这个数据源？" : "启用这个数据源？"}
              onConfirm={() => handleToggleEnabled(record, !record.enabled)}
            >
              <Button type="link">{record.enabled ? "停用" : "启用"}</Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [handleSync, handleTest, handleToggleEnabled, openEditModal]
  );

  return (
    <div className="data-source-page page-shell">
      <div className="page-banner">
        <span className="page-banner__eyebrow">
          <LinkOutlined />
          Remote Metadata Sources
        </span>
        <h1 className="page-banner__title">数据源管理</h1>
        <p className="page-banner__desc">
          统一维护远程数据库连接、测试连通性，并手动同步表结构元数据。分析入口只会使用已启用且测试通过的数据源。
        </p>
        <div className="page-banner__meta">
          <span className="page-banner__pill">当前共 {items.length} 个数据源</span>
          <span className="page-banner__pill">
            已通过测试 {items.filter((item) => item.last_test_status === "success").length} 个
          </span>
        </div>
      </div>

      <Card className="surface-card">
        <Space className="data-source-toolbar" wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            新增数据源
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadDataSources}>
            刷新列表
          </Button>
        </Space>

        <Alert
          className="data-source-tip"
          type="info"
          showIcon
          message="建议新增数据源后先执行“测试连接”，确认连通后再做“同步元数据”。"
        />

        <Table<DataSource>
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          pagination={false}
          scroll={{ x: 1180 }}
        />
      </Card>

      <Modal
        title={editingItem ? "编辑数据源" : "新增数据源"}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="数据源名称" rules={[{ required: true, message: "请输入数据源名称" }]}>
            <Input placeholder="例如：生产 MySQL 主库" />
          </Form.Item>
          <Form.Item name="db_type" label="数据库类型" rules={[{ required: true }]}>
            <Select options={dbTypeOptions} />
          </Form.Item>
          <Form.Item name="host" label="主机地址" rules={[{ required: true, message: "请输入主机地址" }]}>
            <Input placeholder="例如：10.20.30.40" />
          </Form.Item>
          <Form.Item name="port" label="端口" rules={[{ required: true, message: "请输入端口" }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="db_name" label="数据库名称" rules={[{ required: true, message: "请输入数据库名称" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label="用户名" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label={editingItem ? "密码（留空则保持不变）" : "密码"}
            rules={editingItem ? [] : [{ required: true, message: "请输入密码" }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="enabled" label="创建后立即启用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Paragraph className="data-source-form__hint">
            密码会在后端加密存储。若密码有变更，请更新后重新执行一次测试连接。
          </Paragraph>
        </Form>
      </Modal>
    </div>
  );
};
