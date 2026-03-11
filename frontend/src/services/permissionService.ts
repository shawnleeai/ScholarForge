/**
 * Permission Service API
 * 权限管理API客户端
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  permissions_count: number;
  users_count: number;
  created_at: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  code: string;
  description: string;
}

export interface PermissionCheckResult {
  user_id: string;
  resource: string;
  action: string;
  has_permission: boolean;
}

class PermissionService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE}/permissions`;
  }

  // ==================== 角色管理 ====================

  async getRoles(includeSystem: boolean = true): Promise<{ items: Role[]; total: number }> {
    const response = await axios.get(`${this.baseURL}/roles`, {
      params: { include_system: includeSystem }
    });
    return response.data;
  }

  async getRole(roleId: string): Promise<Role> {
    const response = await axios.get(`${this.baseURL}/roles/${roleId}`);
    return response.data;
  }

  async createRole(data: {
    name: string;
    description?: string;
    permission_codes?: string[];
  }): Promise<Role> {
    const response = await axios.post(`${this.baseURL}/roles`, null, {
      params: data
    });
    return response.data;
  }

  async updateRole(roleId: string, data: {
    description?: string;
    permission_codes?: string[];
  }): Promise<Role> {
    const response = await axios.put(`${this.baseURL}/roles/${roleId}`, null, {
      params: data
    });
    return response.data;
  }

  async deleteRole(roleId: string): Promise<void> {
    await axios.delete(`${this.baseURL}/roles/${roleId}`);
  }

  // ==================== 权限管理 ====================

  async getPermissions(resource?: string): Promise<{ items: Permission[]; total: number; grouped: Record<string, Permission[]> }> {
    const response = await axios.get(`${this.baseURL}/permissions`, {
      params: { resource }
    });
    return response.data;
  }

  async createPermission(data: {
    resource: string;
    action: string;
    description?: string;
  }): Promise<Permission> {
    const response = await axios.post(`${this.baseURL}/permissions`, null, {
      params: data
    });
    return response.data;
  }

  // ==================== 用户角色管理 ====================

  async getUserRoles(userId: string): Promise<{ user_id: string; roles: Role[] }> {
    const response = await axios.get(`${this.baseURL}/users/${userId}/roles`);
    return response.data;
  }

  async assignRoleToUser(userId: string, roleId: string): Promise<{ success: boolean }> {
    const response = await axios.post(`${this.baseURL}/users/${userId}/roles`, null, {
      params: { role_id: roleId }
    });
    return response.data;
  }

  async removeRoleFromUser(userId: string, roleId: string): Promise<{ success: boolean }> {
    const response = await axios.delete(`${this.baseURL}/users/${userId}/roles/${roleId}`);
    return response.data;
  }

  async getUserPermissions(userId: string): Promise<{ user_id: string; permissions: string[] }> {
    const response = await axios.get(`${this.baseURL}/users/${userId}/permissions`);
    return response.data;
  }

  // ==================== 权限检查 ====================

  async checkPermission(
    resource: string,
    action: string,
    resourceId?: string
  ): Promise<PermissionCheckResult> {
    const response = await axios.post(`${this.baseURL}/check`, null, {
      params: { resource, action, resource_id: resourceId }
    });
    return response.data;
  }

  // ==================== 资源权限 ====================

  async grantResourcePermission(data: {
    user_id: string;
    resource_type: string;
    resource_id: string;
    permission: string;
    expires_at?: string;
  }): Promise<any> {
    const response = await axios.post(`${this.baseURL}/resource-permissions`, null, {
      params: data
    });
    return response.data;
  }

  async revokeResourcePermission(data: {
    user_id: string;
    resource_type: string;
    resource_id: string;
  }): Promise<{ success: boolean }> {
    const response = await axios.delete(`${this.baseURL}/resource-permissions`, {
      params: data
    });
    return response.data;
  }

  // ==================== 系统初始化 ====================

  async initSystem(): Promise<{ message: string }> {
    const response = await axios.post(`${this.baseURL}/init`);
    return response.data;
  }
}

export const permissionAPI = new PermissionService();
export default permissionAPI;
