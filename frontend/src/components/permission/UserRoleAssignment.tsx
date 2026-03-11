/**
 * User Role Assignment Component
 * 用户角色分配组件 - 管理用户的角色分配
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Select,
  Modal,
  message,
  Avatar,
  Input
} from 'antd';
import {
  UserAddOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { permissionAPI } from '../../services/permissionService';
import styles from './Permission.module.css';

const { Option } = Select;

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  roles: Role[];
}

interface Role {
  id: string;
  name: string;
  description: string;
}

export const UserRoleAssignment: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // 角色颜色映射
  const roleColors: Record<string, string> = {
    'super_admin': 'red',
    'institution_admin': 'orange',
    'advisor': 'blue',
    'student': 'green',
    'reviewer': 'purple',
    'guest': 'default'
  };

  // 角色名称映射
  const roleNames: Record<string, string> = {
    'super_admin': '超级管理员',
    'institution_admin': '机构管理员',
    'advisor': '导师',
    'student': '学生',
    'reviewer': '审稿人',
    'guest': '访客'
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 这里应该调用用户API获取用户列表
      // 简化实现，使用模拟数据
      const mockUsers: User[] = [
        {
          id: '1',
          email: 'admin@scholarforge.com',
          name: '系统管理员',
          roles: [{ id: '1', name: 'super_admin', description: '超级管理员' }]
        },
        {
          id: '2',
          email: 'teacher@university.edu',
          name: '张教授',
          roles: [{ id: '2', name: 'advisor', description: '导师' }]
        },
        {
          id: '3',
          email: 'student@university.edu',
          name: '李同学',
          roles: [{ id: '3', name: 'student', description: '学生' }]
        }
      ];

      const rolesRes = await permissionAPI.getRoles();

      setUsers(mockUsers);
      setRoles(rolesRes.items || []);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRole = (user: User) => {
    setSelectedUser(user);
    setModalVisible(true);
  };

  const handleRemoveRole = async (userId: string, roleId: string) => {
    try {
      await permissionAPI.removeRoleFromUser(userId, roleId);
      message.success('移除角色成功');
      fetchData();
    } catch (error) {
      message.error('移除角色失败');
    }
  };

  const handleRoleChange = async (roleIds: string[]) => {
    if (!selectedUser) return;

    try {
      // 先移除所有现有角色
      for (const role of selectedUser.roles) {
        await permissionAPI.removeRoleFromUser(selectedUser.id, role.id);
      }

      // 添加新角色
      for (const roleId of roleIds) {
        await permissionAPI.assignRoleToUser(selectedUser.id, roleId);
      }

      message.success('角色分配成功');
      setModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('角色分配失败');
    }
  };

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_: any, record: User) => (
        <Space>
          <Avatar src={record.avatar}>
            {record.name?.[0] || record.email[0]}
          </Avatar>
          <div>
            <div>{record.name}</div>
            <div className={styles.userEmail}>{record.email}</div>
          </div>
        </Space>
      )
    },
    {
      title: '角色',
      key: 'roles',
      render: (_: any, record: User) => (
        <Space wrap>
          {record.roles.map(role => (
            <Tag
              key={role.id}
              color={roleColors[role.name] || 'default'}
              closable
              onClose={() => handleRemoveRole(record.id, role.id)}
            >
              {roleNames[role.name] || role.name}
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: User) => (
        <Button
          type="primary"
          size="small"
          icon={<UserAddOutlined />}
          onClick={() => handleAssignRole(record)}
        >
          分配角色
        </Button>
      )
    }
  ];

  return (
    <Card
      className={styles.userRoleAssignment}
      title="用户角色管理"
      extra={
        <Input
          placeholder="搜索用户"
          prefix={<SearchOutlined />}
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          style={{ width: 200 }}
          allowClear
        />
      }
    >
      <Table
        columns={columns}
        dataSource={filteredUsers}
        loading={loading}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={`为 ${selectedUser?.name} 分配角色`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="选择角色"
          defaultValue={selectedUser?.roles.map(r => r.id)}
          onChange={handleRoleChange}
        >
          {roles.map(role => (
            <Option key={role.id} value={role.id}>
              <Tag color={roleColors[role.name] || 'default'}>
                {roleNames[role.name] || role.name}
              </Tag>
              <span className={styles.roleDescription}>{role.description}</span>
            </Option>
          ))}
        </Select>
      </Modal>
    </Card>
  );
};

export default UserRoleAssignment;
