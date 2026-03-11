/**
 * Notification Page
 * 通知中心页面 - 查看和管理所有通知
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  List,
  Button,
  Tabs,
  Tag,
  Empty,
  Skeleton,
  message,
  Popconfirm,
  Badge,
  Typography,
  Space,
  Segmented
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ClearOutlined,
  SettingOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  CommentOutlined,
  TeamOutlined,
  RobotOutlined,
  FileTextOutlined,
  MailOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { notificationAPI, Notification } from '../../services/notificationService';
import { NotificationSettings } from '../../components/notification';
import styles from './NotificationPage.module.css';

const { Title } = Typography;
const { TabPane } = Tabs;

// 通知类型配置
const notificationConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  paper_comment: { icon: <CommentOutlined />, color: '#1890ff', label: '批注' },
  paper_mention: { icon: <MailOutlined />, color: '#fa8c16', label: '提及' },
  paper_shared: { icon: <TeamOutlined />, color: '#52c41a', label: '分享' },
  collab_invite: { icon: <TeamOutlined />, color: '#722ed1', label: '协作' },
  ai_analysis_complete: { icon: <RobotOutlined />, color: '#eb2f96', label: 'AI' },
  ai_suggestion: { icon: <RobotOutlined />, color: '#13c2c2', label: '建议' },
  submission_accepted: { icon: <FileTextOutlined />, color: '#52c41a', label: '投稿' },
  system_maintenance: { icon: <InfoCircleOutlined />, color: '#faad14', label: '系统' },
  welcome: { icon: <InfoCircleOutlined />, color: '#1890ff', label: '欢迎' }
};

const NotificationPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [showSettings, setShowSettings] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const unreadOnly = activeTab === 'unread';
      const response = await notificationAPI.getNotifications(unreadOnly, 50);
      setNotifications(response.items || []);
      setUnreadCount(response.unread_count || 0);
    } catch (error) {
      message.error('获取通知失败');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationAPI.markAsRead(notificationId);
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      message.error('标记已读失败');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationAPI.markAllAsRead();
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
      message.success('已全部标记为已读');
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDelete = async (notificationId: string) => {
    try {
      await notificationAPI.deleteNotification(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleClearAll = async () => {
    try {
      await notificationAPI.clearAll();
      setNotifications([]);
      setUnreadCount(0);
      message.success('已清空所有通知');
    } catch (error) {
      message.error('操作失败');
    }
  };

  const renderNotificationItem = (item: Notification) => {
    const config = notificationConfig[item.type] || {
      icon: <InfoCircleOutlined />,
      color: '#999',
      label: '通知'
    };

    return (
      <List.Item
        className={`${styles.notificationItem} ${!item.is_read ? styles.unread : ''}`}
        actions={[
          !item.is_read && (
            <Button
              key="read"
              type="text"
              icon={<CheckOutlined />}
              onClick={() => handleMarkAsRead(item.id)}
            >
              标记已读
            </Button>
          ),
          <Popconfirm
            key="delete"
            title="确定删除此通知？"
            onConfirm={() => handleDelete(item.id)}
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        ]}
      >
        <List.Item.Meta
          avatar={
            <div
              className={styles.typeIcon}
              style={{ background: `${config.color}20`, color: config.color }}
            >
              {config.icon}
            </div>
          }
          title={
            <div className={styles.itemTitle}>
              <span>{item.title}</span>
              {!item.is_read && <Badge status="processing" color="#667eea" />}
            </div>
          }
          description={
            <div>
              <div className={styles.itemContent}>{item.content}</div>
              <Space className={styles.itemMeta}>
                <Tag color={config.color}>{config.label}</Tag>
                <span className={styles.time}>
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </Space>
            </div>
          }
        />
      </List.Item>
    );
  };

  if (showSettings) {
    return (
      <div className={styles.notificationPage}>
        <div className={styles.pageHeader}>
          <Title level={4}>
            <SettingOutlined /> 通知设置
          </Title>
          <Button onClick={() => setShowSettings(false)}>
            返回通知列表
          </Button>
        </div>
        <NotificationSettings />
      </div>
    );
  }

  return (
    <div className={styles.notificationPage}>
      <div className={styles.pageHeader}>
        <Title level={4}>
          <BellOutlined /> 通知中心
          {unreadCount > 0 && (
            <Badge
              count={unreadCount}
              style={{ marginLeft: 12 }}
            />
          )}
        </Title>
        <Space>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowSettings(true)}
          >
            通知设置
          </Button>
          {unreadCount > 0 && (
            <Button
              icon={<CheckCircleOutlined />}
              onClick={handleMarkAllAsRead}
            >
              全部已读
            </Button>
          )}
          <Popconfirm
            title="确定清空所有通知？"
            onConfirm={handleClearAll}
          >
            <Button danger icon={<ClearOutlined />}>
              清空全部
            </Button>
          </Popconfirm>
        </Space>
      </div>

      <Card>
        <div className={styles.filterBar}>
          <Segmented
            value={activeTab}
            onChange={setActiveTab}
            options={[
              { label: '全部通知', value: 'all' },
              { label: `未读 (${unreadCount})`, value: 'unread' }
            ]}
          />
        </div>

        {loading ? (
          <div className={styles.skeletonList}>
            {[1, 2, 3, 4, 5].map(i => (
              <Skeleton key={i} avatar paragraph={{ rows: 2 }} active />
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={activeTab === 'unread' ? '没有未读通知' : '暂无通知'}
          />
        ) : (
          <List
            dataSource={notifications}
            renderItem={renderNotificationItem}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: total => `共 ${total} 条通知`
            }}
          />
        )}
      </Card>
    </div>
  );
};

export default NotificationPage;
