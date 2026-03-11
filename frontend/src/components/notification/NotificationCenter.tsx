/**
 * Notification Center Component
 * 通知中心组件 - 展示和管理用户通知
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Badge,
  Dropdown,
  List,
  Avatar,
  Button,
  Empty,
  Tabs,
  Typography,
  Tag,
  Skeleton,
  message,
  Popconfirm
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ClearOutlined,
  CommentOutlined,
  TeamOutlined,
  RobotOutlined,
  FileTextOutlined,
  MailOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { notificationAPI, Notification } from '../../services/notificationService';
import styles from './Notification.module.css';

const { TabPane } = Tabs;
const { Text } = Typography;

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

interface NotificationCenterProps {
  userId: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ userId }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  // 获取通知列表
  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await notificationAPI.getNotifications(activeTab === 'unread');
      setNotifications(response.items || []);
      setUnreadCount(response.unread_count || 0);
    } catch (error) {
      console.error('获取通知失败:', error);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  // 获取未读数量
  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await notificationAPI.getUnreadCount();
      setUnreadCount(response.unread_count || 0);
    } catch (error) {
      console.error('获取未读数量失败:', error);
    }
  }, []);

  // WebSocket连接
  useEffect(() => {
    const ws = notificationAPI.connectWebSocket(userId, {
      onMessage: (data) => {
        if (data.type === 'notification') {
          // 新通知到达
          setNotifications(prev => [data.data, ...prev]);
          setUnreadCount(prev => prev + 1);

          // 显示浏览器通知
          if (Notification.permission === 'granted') {
            new Notification(data.data.title, {
              body: data.data.content,
              icon: '/logo.png'
            });
          }
        }
      },
      onConnect: () => setWsConnected(true),
      onDisconnect: () => setWsConnected(false)
    });

    return () => {
      ws?.close();
    };
  }, [userId]);

  // 初始加载和标签切换时获取通知
  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // 定期刷新未读数量
  useEffect(() => {
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // 标记已读
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

  // 标记全部已读
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

  // 删除通知
  const handleDelete = async (notificationId: string) => {
    try {
      await notificationAPI.deleteNotification(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 清空所有通知
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

  // 渲染通知项
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
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleMarkAsRead(item.id)}
            />
          ),
          <Popconfirm
            key="delete"
            title="确定删除此通知？"
            onConfirm={() => handleDelete(item.id)}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        ]}
      >
        <List.Item.Meta
          avatar={
            <Avatar
              style={{ backgroundColor: config.color }}
              icon={config.icon}
            />
          }
          title={
            <div className={styles.notificationTitle}>
              <Text strong={!item.is_read}>{item.title}</Text>
              {!item.is_read && <span className={styles.unreadDot} />}
            </div>
          }
          description={
            <div>
              <Text type="secondary" className={styles.notificationContent}>
                {item.content}
              </Text>
              <div className={styles.notificationMeta}>
                <Tag size="small" color={config.color}>
                  {config.label}
                </Tag>
                <Text type="secondary" className={styles.time}>
                  {new Date(item.created_at).toLocaleString()}
                </Text>
              </div>
            </div>
          }
        />
      </List.Item>
    );
  };

  // 通知下拉面板
  const notificationPanel = (
    <div className={styles.notificationPanel}>
      <div className={styles.panelHeader}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="small"
          className={styles.tabs}
        >
          <TabPane tab="全部" key="all" />
          <TabPane tab={`未读 (${unreadCount})`} key="unread" />
        </Tabs>
        <div className={styles.panelActions}>
          {unreadCount > 0 && (
            <Button
              type="text"
              size="small"
              icon={<CheckOutlined />}
              onClick={handleMarkAllAsRead}
            >
              全部已读
            </Button>
          )}
          <Popconfirm
            title="确定清空所有通知？"
            onConfirm={handleClearAll}
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<ClearOutlined />}
            >
              清空
            </Button>
          </Popconfirm>
        </div>
      </div>

      <div className={styles.notificationList}>
        {loading ? (
          <div className={styles.skeletonList}>
            {[1, 2, 3].map(i => (
              <Skeleton key={i} avatar paragraph={{ rows: 2 }} active />
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无通知"
            className={styles.empty}
          />
        ) : (
          <List
            dataSource={notifications}
            renderItem={renderNotificationItem}
            className={styles.list}
          />
        )}
      </div>

      <div className={styles.panelFooter}>
        <Text type="secondary" className={styles.wsStatus}>
          {wsConnected ? '🟢 实时连接' : '🔴 离线'}
        </Text>
        <Button type="link" size="small">
          查看全部通知
        </Button>
      </div>
    </div>
  );

  return (
    <Dropdown
      overlay={notificationPanel}
      trigger={['click']}
      placement="bottomRight"
      overlayClassName={styles.dropdown}
    >
      <Badge count={unreadCount} overflowCount={99} offset={[-2, 2]}>
        <Button
          type="text"
          icon={<BellOutlined />}
          className={styles.bellButton}
        />
      </Badge>
    </Dropdown>
  );
};

export default NotificationCenter;
