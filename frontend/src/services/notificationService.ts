/**
 * Notification Service API
 * 通知服务API客户端
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  content: string;
  data: Record<string, any>;
  sender_id?: string;
  related_type?: string;
  related_id?: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export interface NotificationPreferences {
  channels: {
    in_app: boolean;
    email: boolean;
    web_push: boolean;
    sms: boolean;
  };
  preferences: Record<string, string[]>;
}

interface WebSocketCallbacks {
  onMessage?: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

class NotificationService {
  private baseURL: string;
  private ws: WebSocket | null = null;

  constructor() {
    this.baseURL = `${API_BASE}/notifications`;
  }

  // ==================== REST API ====================

  async getNotifications(unreadOnly: boolean = false, limit: number = 20, offset: number = 0): Promise<{
    items: Notification[];
    unread_count: number;
    limit: number;
    offset: number;
  }> {
    const response = await axios.get(this.baseURL + '/', {
      params: { unread_only: unreadOnly, limit, offset }
    });
    return response.data;
  }

  async getUnreadCount(): Promise<{ unread_count: number }> {
    const response = await axios.get(`${this.baseURL}/unread-count`);
    return response.data;
  }

  async markAsRead(notificationId: string): Promise<{ success: boolean }> {
    const response = await axios.post(`${this.baseURL}/${notificationId}/read`);
    return response.data;
  }

  async markAllAsRead(): Promise<{ success: boolean }> {
    const response = await axios.post(`${this.baseURL}/read-all`);
    return response.data;
  }

  async deleteNotification(notificationId: string): Promise<{ success: boolean }> {
    const response = await axios.delete(`${this.baseURL}/${notificationId}`);
    return response.data;
  }

  async clearAll(): Promise<{ success: boolean }> {
    const response = await axios.delete(this.baseURL + '/');
    return response.data;
  }

  // ==================== 偏好设置 ====================

  async getPreferences(): Promise<NotificationPreferences> {
    const response = await axios.get(`${this.baseURL}/preferences`);
    return response.data;
  }

  async updatePreferences(preferences: NotificationPreferences): Promise<{
    user_id: string;
    preferences: NotificationPreferences;
    updated: boolean;
  }> {
    const response = await axios.put(`${this.baseURL}/preferences`, preferences);
    return response.data;
  }

  // ==================== WebSocket ====================

  connectWebSocket(userId: string, callbacks: WebSocketCallbacks): WebSocket {
    const wsURL = API_BASE.replace('http', 'ws') + `/notifications/ws/${userId}`;
    this.ws = new WebSocket(wsURL);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      callbacks.onConnect?.();

      // 发送认证消息
      this.ws?.send(JSON.stringify({
        type: 'auth',
        data: { user_id: userId }
      }));
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callbacks.onMessage?.(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      callbacks.onDisconnect?.();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      callbacks.onError?.(error);
    };

    return this.ws;
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // ==================== 测试/开发方法 ====================

  async sendTestNotification(type: string = 'welcome'): Promise<{ message: string }> {
    const response = await axios.post(`${this.baseURL}/test`, null, {
      params: { type }
    });
    return response.data;
  }

  async getOnlineUsers(): Promise<{ count: number; users: any[] }> {
    const response = await axios.get(`${this.baseURL}/online-users`);
    return response.data;
  }
}

export const notificationAPI = new NotificationService();
export default notificationAPI;
