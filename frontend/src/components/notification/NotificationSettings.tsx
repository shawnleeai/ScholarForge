/**
 * Notification Settings Component
 * 通知设置组件 - 管理通知偏好设置
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Switch,
  Table,
  Tag,
  Button,
  message,
  Alert,
  Space,
  Checkbox,
  Tooltip
} from 'antd';
import {
  BellOutlined,
  MailOutlined,
  MobileOutlined,
  DesktopOutlined,
  MessageOutlined,
  InfoCircleOutlined,
  SaveOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { notificationAPI, NotificationPreferences } from '../../services/notificationService';
import styles from './Notification.module.css';

// 通知类型配置
const notificationTypes = [
  {
    key: 'paper_comment',
    name: '论文批注',
    description: '当有人给你的论文添加批注时',
    icon: <MessageOutlined />,
    color: '#1890ff'
  },
  {
    key: 'paper_mention',
    name: '被@提及',
    description: '当有人在评论中@你时',
    icon: <MailOutlined />,
    color: '#fa8c16'
  },
  {
    key: 'collab_invite',
    name: '协作邀请',
    description: '当有人邀请你协作编辑时',
    icon: <BellOutlined />,
    color: '#722ed1'
  },
  {
    key: 'ai_analysis_complete',
    name: 'AI分析完成',
    description: '当AI分析任务完成时',
    icon: <DesktopOutlined />,
    color: '#eb2f96'
  },
  {
    key: 'submission_reviewed',
    name: '审稿意见',
    description: '当收到审稿意见时',
    icon: <MailOutlined />,
    color: '#52c41a'
  },
  {
    key: 'system_maintenance',
    name: '系统维护',
    description: '系统维护通知',
    icon: <InfoCircleOutlined />,
    color: '#faad14'
  }
];

// 通知渠道配置
const channels = [
  {
    key: 'in_app',
    name: '站内消息',
    description: '在应用内显示通知',
    icon: <BellOutlined />,
    color: '#1890ff'
  },
  {
    key: 'email',
    name: '邮件通知',
    description: '发送邮件到你的注册邮箱',
    icon: <MailOutlined />,
    color: '#52c41a'
  },
  {
    key: 'web_push',
    name: '浏览器推送',
    description: '桌面浏览器推送通知',
    icon: <DesktopOutlined />,
    color: '#722ed1'
  },
  {
    key: 'sms',
    name: '短信通知',
    description: '发送短信到你的手机',
    icon: <MobileOutlined />,
    color: '#fa8c16'
  }
];

export const NotificationSettings: React.FC = () => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    channels: {
      in_app: true,
      email: true,
      web_push: false,
      sms: false
    },
    preferences: {}
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    setLoading(true);
    try {
      const data = await notificationAPI.getPreferences();
      setPreferences(data);
    } catch (error) {
      message.error('获取设置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await notificationAPI.updatePreferences(preferences);
      message.success('设置已保存');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleChannelToggle = (channel: string, checked: boolean) => {
    setPreferences(prev => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: checked
      }
    }));
  };

  const handlePreferenceChange = (type: string, channel: string, checked: boolean) => {
    setPreferences(prev => {
      const currentChannels = prev.preferences[type] || [];
      const newChannels = checked
        ? [...currentChannels, channel]
        : currentChannels.filter(c => c !== channel);

      return {
        ...prev,
        preferences: {
          ...prev.preferences,
          [type]: newChannels
        }
      };
    });
  };

  // 请求浏览器通知权限
  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      message.error('您的浏览器不支持桌面通知');
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      message.success('已开启浏览器通知权限');
      handleChannelToggle('web_push', true);
    } else {
      message.warning('请允许浏览器通知权限');
    }
  };

  const columns = [
    {
      title: '通知类型',
      dataIndex: 'key',
      key: 'type',
      render: (key: string) => {
        const type = notificationTypes.find(t => t.key === key);
        return (
          <div className={styles.notificationType}>
            <div
              className={styles.typeIcon}
              style={{ background: type?.color }}
            >
              {type?.icon}
            </div>
            <div>
              <div className={styles.typeName}>{type?.name}</div>
              <div className={styles.typeDesc}>{type?.description}</div>
            </div>
          </div>
        );
      }
    },
    ...channels.map(channel => ({
      title: (
        <Tooltip title={channel.description}>
          <Space>
            {channel.icon}
            {channel.name}
          </Space>
        </Tooltip>
      ),
      key: channel.key,
      align: 'center' as const,
      render: (_: any, record: { key: string }) => (
        <Checkbox
          checked={preferences.preferences[record.key]?.includes(channel.key)}
          onChange={e =>
            handlePreferenceChange(record.key, channel.key, e.target.checked)
          }
          disabled={!preferences.channels[channel.key as keyof typeof preferences.channels]}
        />
      )
    }))
  ];

  return (
    <Card
      className={styles.settingsCard}
      title={
        <Space>
          <BellOutlined />
          通知设置
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchPreferences}
            loading={loading}
          >
            重置
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
      loading={loading}
    >
      <Alert
        message="通知偏好设置"
        description="自定义您接收通知的方式。请先启用通知渠道，然后为每种通知类型选择接收方式。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 渠道设置 */}
      <div className={styles.channelSection}>
        <h4>通知渠道</h4>
        <div className={styles.channelGrid}>
          {channels.map(channel => (
            <div
              key={channel.key}
              className={`${styles.channelCard} ${
                preferences.channels[channel.key as keyof typeof preferences.channels]
                  ? styles.active
                  : ''
              }`}
            >
              <div
                className={styles.channelIcon}
                style={{ background: `${channel.color}20`, color: channel.color }}
              >
                {channel.icon}
              </div>
              <div className={styles.channelInfo}>
                <div className={styles.channelName}>{channel.name}</div>
                <div className={styles.channelDesc}>{channel.description}</div>
              </div>
              <Switch
                checked={preferences.channels[channel.key as keyof typeof preferences.channels]}
                onChange={checked => {
                  if (channel.key === 'web_push' && checked) {
                    requestNotificationPermission();
                  } else {
                    handleChannelToggle(channel.key, checked);
                  }
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* 通知类型偏好 */}
      <div className={styles.channelSection}>
        <h4>通知类型偏好</h4>
        <Table
          columns={columns}
          dataSource={notificationTypes}
          rowKey="key"
          pagination={false}
          size="small"
          bordered
        />
      </div>

      {/* 提示信息 */}
      <Alert
        message="提示"
        description={
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>站内消息：无论设置如何，重要系统消息都会通过站内消息发送</li>
            <li>邮件通知：每天最多发送50封邮件，超出部分将延迟到次日</li>
            <li>浏览器推送：需要保持浏览器开启，且已授予通知权限</li>
            <li>短信通知：仅用于紧急安全提醒，普通通知不会发送短信</li>
          </ul>
        }
        type="warning"
        showIcon
        style={{ marginTop: 24 }}
      />
    </Card>
  );
};

export default NotificationSettings;
