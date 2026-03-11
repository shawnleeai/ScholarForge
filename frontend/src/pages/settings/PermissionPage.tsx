/**
 * Permission Management Page
 * 权限管理页面 - 系统管理员管理角色和权限
 */

import React, { useState } from 'react';
import {
  Tabs,
  Card,
  Row,
  Col,
  Statistic,
  Alert,
  Button,
  message
} from 'antd';
import {
  TeamOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import {
  RoleManager,
  PermissionMatrix,
  UserRoleAssignment
} from '../../components/permission';
import { permissionAPI } from '../../services/permissionService';
import styles from './PermissionPage.module.css';

const { TabPane } = Tabs;

const PermissionPage: React.FC = () => {
  const [initLoading, setInitLoading] = useState(false);

  const handleInitSystem = async () => {
    setInitLoading(true);
    try {
      await permissionAPI.initSystem();
      message.success('系统角色和权限初始化成功');
    } catch (error) {
      message.error('初始化失败，请检查权限');
    } finally {
      setInitLoading(false);
    }
  };

  return (
    <div className={styles.permissionPage}>
      <div className={styles.permissionPageHeader}>
        <h1 className={styles.permissionPageTitle}>
          <SafetyCertificateOutlined /> 权限管理中心
        </h1>
        <p className={styles.permissionPageSubtitle}>
          管理系统的角色、权限和用户访问控制
        </p>
      </div>

      <Alert
        message="权限管理说明"
        description="系统使用RBAC（基于角色的访问控制）模型。您可以创建自定义角色、分配权限给用户、以及管理资源级别的访问控制。超级管理员拥有所有权限。"
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: 24 }}
        action={
          <Button
            size="small"
            type="primary"
            ghost
            onClick={handleInitSystem}
            loading={initLoading}
          >
            初始化系统权限
          </Button>
        }
      />

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card className={styles.statsCard}>
            <Statistic
              title="系统角色"
              value={6}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#fff' }}
            />
            <div className={styles.statsCardLabel}>预定义角色</div>
          </Card>
        </Col>
        <Col span={8}>
          <Card className={styles.statsCard} style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <Statistic
              title="权限数量"
              value={18}
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#fff' }}
            />
            <div className={styles.statsCardLabel}>可分配权限</div>
          </Card>
        </Col>
        <Col span={8}>
          <Card className={styles.statsCard} style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <Statistic
              title="已分配用户"
              value={128}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#fff' }}
            />
            <div className={styles.statsCardLabel}>带有角色的用户</div>
          </Card>
        </Col>
      </Row>

      <Tabs
        defaultActiveKey="roles"
        className={styles.permissionTabs}
        type="card"
      >
        <TabPane
          tab={<span><TeamOutlined /> 角色管理</span>}
          key="roles"
        >
          <RoleManager />
        </TabPane>

        <TabPane
          tab={<span><SafetyCertificateOutlined /> 权限矩阵</span>}
          key="matrix"
        >
          <PermissionMatrix />
        </TabPane>

        <TabPane
          tab={<span><UserOutlined /> 用户角色分配</span>}
          key="users"
        >
          <UserRoleAssignment />
        </TabPane>
      </Tabs>

      <Card style={{ marginTop: 24 }}>
        <div className={styles.permissionHelp}>
          <h4><SettingOutlined /> 快速帮助</h4>
          <ul>
            <li><strong>角色</strong>：一组权限的集合，如"学生"、"导师"、"管理员"</li>
            <li><strong>权限</strong>：对特定资源的操作许可，如"paper:create"、"paper:read"</li>
            <li><strong>资源权限</strong>：针对特定资源实例的权限，如某篇论文的协作者</li>
            <li><strong>系统角色</strong>：预定义角色不可删除，但可修改权限</li>
            <li><strong>权限检查顺序</strong>：超级管理员 {'>'} 角色权限 {'>'} 资源权限</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

export default PermissionPage;
