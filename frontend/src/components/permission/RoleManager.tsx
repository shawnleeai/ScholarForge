/**
 * Role Manager Component
 * 角色管理组件 - 用于系统管理员管理角色和权限
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Descriptions,
  Transfer,
  Popconfirm,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UserOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { permissionAPI } from '../../services/permissionService';
import styles from './Permission.module.css';

const { Option } = Select;

interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  permissions_count: number;
  users_count: number;
  created_at: string;
}

interface Permission {
  id: string;
  resource: string;
  action: string;
  code: string;
  description: string;
}

export const RoleManager: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [form] = Form.useForm();
  const [transferTargetKeys, setTransferTargetKeys] = useState<string[]>([]);

  // 预定义角色颜色映射
  const roleColors: Record<string, string> = {
    'super_admin': 'red',
    'institution_admin': 'orange',
    'advisor': 'blue',
    'student': 'green',
    'reviewer': 'purple',
    'guest': 'default'
  };

  // 预定义角色名称映射
  const roleNames: Record<string, string> = {
    'super_admin': '超级管理员',
    'institution_admin': '机构管理员',
    'advisor': '导师',
    'student': '学生',
    'reviewer': '审稿人',
    'guest': '访客'
  };

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, []);

  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await permissionAPI.getRoles();
      setRoles(response.items || []);
    } catch (error) {
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchPermissions = async () => {
    try {
      const response = await permissionAPI.getPermissions();
      setPermissions(response.items || []);
    } catch (error) {
      message.error('获取权限列表失败');
    }
  };

  const handleCreate = () => {
    setEditingRole(null);
    form.resetFields();
    setTransferTargetKeys([]);
    setModalVisible(true);
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue({
      name: role.name,
      description: role.description,
      is_active: role.is_active
    });
    // 这里应该获取角色的权限列表
    setTransferTargetKeys([]);
    setModalVisible(true);
  };

  const handleViewDetail = async (role: Role) => {
    try {
      const detail = await permissionAPI.getRole(role.id);
      setSelectedRole(detail);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('获取角色详情失败');
    }
  };

  const handleDelete = async (roleId: string) => {
    try {
      await permissionAPI.deleteRole(roleId);
      message.success('删除成功');
      fetchRoles();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const permissionCodes = transferTargetKeys.map(key => {
        const perm = permissions.find(p => p.id === key);
        return perm ? `${perm.resource}:${perm.action}` : '';
      }).filter(Boolean);

      if (editingRole) {
        await permissionAPI.updateRole(editingRole.id, {
          description: values.description,
          permission_codes: permissionCodes
        });
        message.success('更新成功');
      } else {
        await permissionAPI.createRole({
          name: values.name,
          description: values.description,
          permission_codes: permissionCodes
        });
        message.success('创建成功');
      }

      setModalVisible(false);
      fetchRoles();
    } catch (error) {
      message.error(editingRole ? '更新失败' : '创建失败');
    }
  };

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Tag color={roleColors[name] || 'default'}>
          {roleNames[name] || name}
        </Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'is_system',
      key: 'is_system',
      render: (isSystem: boolean) => (
        isSystem ?
          <Badge status="processing" text="系统角色" /> :
          <Badge status="default" text="自定义" />
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Switch
          checked={isActive}
          size="small"
          disabled
        />
      )
    },
    {
      title: '权限数',
      dataIndex: 'permissions_count',
      key: 'permissions_count',
      render: (count: number) => (
        <Tag icon={<SafetyCertificateOutlined />} color="blue">
          {count} 个权限
        </Tag>
      )
    },
    {
      title: '用户数',
      dataIndex: 'users_count',
      key: 'users_count',
      render: (count: number) => (
        <Tag icon={<UserOutlined />} color="green">
          {count} 个用户
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Role) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled={record.is_system}
          />
          <Popconfirm
            title="确定删除此角色吗？"
            onConfirm={() => handleDelete(record.id)}
            disabled={record.is_system}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_system}
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  const transferData = permissions.map(perm => ({
    key: perm.id,
    title: `${perm.resource}:${perm.action}`,
    description: perm.description
  }));

  return (
    <div className={styles.roleManager}>
      <Card
        title="角色管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            新建角色
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={roles}
          loading={loading}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>

      {/* 创建/编辑角色模态框 */}
      <Modal
        title={editingRole ? '编辑角色' : '新建角色'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => setModalVisible(false)}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input
              disabled={!!editingRole}
              placeholder="如：custom_role"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea
              rows={2}
              placeholder="角色描述信息"
            />
          </Form.Item>

          <Form.Item label="权限分配">
            <Transfer
              dataSource={transferData}
              titles={['可用权限', '已分配权限']}
              targetKeys={transferTargetKeys}
              onChange={setTransferTargetKeys}
              render={item => item.title}
              listStyle={{
                width: 280,
                height: 300
              }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 角色详情模态框 */}
      <Modal
        title="角色详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedRole && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="角色名称">
              {roleNames[selectedRole.name] || selectedRole.name}
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {selectedRole.description}
            </Descriptions.Item>
            <Descriptions.Item label="权限列表">
              <Space wrap>
                {selectedRole.permissions?.map((perm: any) => (
                  <Tag key={perm.id} color="blue">
                    {perm.resource}:{perm.action}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="分配用户">
              <Space wrap>
                {selectedRole.users?.map((user: any) => (
                  <Tag key={user.id} icon={<UserOutlined />}>
                    {user.name || user.email}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default RoleManager;
