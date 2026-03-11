/**
 * Permission Matrix Component
 * 权限矩阵组件 - 展示资源和操作的权限关系
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Checkbox,
  Tag,
  Space,
  Button,
  message,
  Tooltip
} from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { permissionAPI } from '../../services/permissionService';
import styles from './Permission.module.css';

interface Permission {
  id: string;
  resource: string;
  action: string;
  code: string;
  description: string;
}

interface Role {
  id: string;
  name: string;
  is_system: boolean;
}

export const PermissionMatrix: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [matrix, setMatrix] = useState<Record<string, Set<string>>>({});

  // 资源分组
  const resourceGroups: Record<string, string> = {
    'paper': '论文',
    'team': '团队',
    'ai': 'AI功能',
    'dataset': '数据集',
    'system': '系统',
    'user': '用户管理'
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rolesRes, permsRes] = await Promise.all([
        permissionAPI.getRoles(),
        permissionAPI.getPermissions()
      ]);

      setRoles(rolesRes.items || []);
      setPermissions(permsRes.items || []);

      // 初始化权限矩阵
      const initialMatrix: Record<string, Set<string>> = {};
      (rolesRes.items || []).forEach((role: Role) => {
        initialMatrix[role.id] = new Set();
      });
      setMatrix(initialMatrix);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionChange = (roleId: string, permCode: string, checked: boolean) => {
    setMatrix(prev => {
      const newMatrix = { ...prev };
      if (!newMatrix[roleId]) {
        newMatrix[roleId] = new Set();
      }

      if (checked) {
        newMatrix[roleId].add(permCode);
      } else {
        newMatrix[roleId].delete(permCode);
      }

      return newMatrix;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // 批量保存权限设置
      const promises = Object.entries(matrix).map(([roleId, permCodes]) =>
        permissionAPI.updateRole(roleId, {
          permission_codes: Array.from(permCodes)
        })
      );

      await Promise.all(promises);
      message.success('权限设置已保存');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  // 按资源分组权限
  const groupedPermissions = permissions.reduce((acc, perm) => {
    if (!acc[perm.resource]) {
      acc[perm.resource] = [];
    }
    acc[perm.resource].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  // 表格列定义
  const columns = [
    {
      title: '资源',
      dataIndex: 'resource',
      key: 'resource',
      width: 120,
      render: (resource: string) => (
        <Tag color="blue">{resourceGroups[resource] || resource}</Tag>
      )
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 100
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    ...roles.map(role => ({
      title: (
        <Tooltip title={role.is_system ? '系统角色' : '自定义角色'}>
          <Tag color={role.is_system ? 'red' : 'default'}>
            {role.name}
          </Tag>
        </Tooltip>
      ),
      key: role.id,
      width: 100,
      align: 'center' as const,
      render: (_: any, record: Permission) => (
        <Checkbox
          checked={matrix[role.id]?.has(record.code)}
          onChange={e => handlePermissionChange(role.id, record.code, e.target.checked)}
          disabled={role.is_system && role.name === 'super_admin'}
        />
      )
    }))
  ];

  // 扁平化数据
  const tableData = Object.entries(groupedPermissions).flatMap(([resource, perms]) =>
    perms.map(perm => ({
      ...perm,
      resource
    }))
  );

  return (
    <Card
      className={styles.permissionMatrix}
      title="权限矩阵"
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchData}
            loading={loading}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
          >
            保存设置
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={tableData}
        loading={loading}
        rowKey="id"
        size="small"
        pagination={false}
        scroll={{ x: 'max-content' }}
      />

      <div className={styles.legend}>
        <Space>
          <span>图例：</span>
          <Tag color="red">系统角色</Tag>
          <Tag>自定义角色</Tag>
        </Space>
      </div>
    </Card>
  );
};

export default PermissionMatrix;
