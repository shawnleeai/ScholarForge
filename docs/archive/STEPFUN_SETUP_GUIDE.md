# 阶跃星辰 (StepFun) API Key 配置指南

> 文档日期：2026-03-04
> 适用版本：ScholarForge v0.1.0+

---

## 一、获取 API Key

### 1.1 注册账号

1. 访问阶跃星辰开放平台：https://platform.stepfun.com/
2. 点击右上角「注册」按钮
3. 使用手机号或邮箱注册账号
4. 完成实名认证（需要身份证信息）

### 1.2 创建应用获取 API Key

1. 登录后进入「控制台」
2. 点击左侧菜单「应用管理」
3. 点击「创建应用」按钮
4. 填写应用信息：
   - 应用名称：ScholarForge（或自定义）
   - 应用描述：学术研究助手
   - 应用类型：其他
5. 创建成功后，点击应用进入详情页
6. 复制「API Key」（以 `step-` 开头）

### 1.3 查看模型权限

在应用详情页，确认已开通以下模型权限：
- ✅ step-1-8k
- ✅ step-1-32k
- ✅ step-1-128k
- ✅ step-1-256k
- ✅ step-2-16k
- ✅ step-2-200k

> **注意**：新注册的账号可能需要申请开通，一般1-2个工作日内审核完成。

---

## 二、配置 API Key

### 2.1 方法一：环境变量配置（推荐）

1. 在项目根目录创建 `.env` 文件：

```bash
cd D:/Github/coding/ScholarForge

# 复制示例文件
copy .env.example .env
```

2. 编辑 `.env` 文件，添加阶跃星辰配置：

```env
# ============================================
# 阶跃星辰 / StepFun 配置
# ============================================
STEPFUN_API_KEY=step-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STEPFUN_MODEL=step-1-8k

# 设置为默认AI提供商（可选）
AI_DEFAULT_PROVIDER=stepfun
AI_FALLBACK_ENABLED=true
```

### 2.2 方法二：后端配置文件

直接编辑 `backend/shared/config.py`：

```python
# 在 Settings 类中添加
stepfun_api_key: Optional[str] = "step-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
stepfun_model: str = "step-1-8k"
```

> **不推荐**：会留下敏感信息在代码中

### 2.3 方法三：运行时环境变量

Windows PowerShell:
```powershell
$env:STEPFUN_API_KEY="step-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:AI_DEFAULT_PROVIDER="stepfun"

# 然后启动服务
cd backend
python run.py ai
```

Windows CMD:
```cmd
set STEPFUN_API_KEY=step-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set AI_DEFAULT_PROVIDER=stepfun

cd backend
python run.py ai
```

Linux/Mac:
```bash
export STEPFUN_API_KEY=step-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export AI_DEFAULT_PROVIDER=stepfun

cd backend
python run.py ai
```

---

## 三、验证配置

### 3.1 启动服务

```bash
# 1. 启动AI服务
cd D:/Github/coding/ScholarForge/backend
python run.py ai

# 2. 启动网关（新终端）
cd D:/Github/coding/ScholarForge/backend
python run.py gateway

# 3. 启动前端（新终端）
cd D:/Github/coding/ScholarForge/frontend
npm run dev
```

### 3.2 测试API

使用 curl 或浏览器访问健康检查接口：

```bash
curl http://localhost:8000/api/v1/ai/health
```

预期响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "providers": [
      {
        "provider": "stepfun",
        "status": "healthy",
        "latency_ms": 150,
        "supported_models": ["step-1-8k", "step-1-32k", ...]
      }
    ]
  }
}
```

### 3.3 前端测试

1. 打开浏览器访问：http://localhost:5173
2. 登录账号
3. 打开任意论文编辑页面
4. 点击右侧「AI助手」面板
5. 选择「写作助手」标签
6. 输入文本并点击「续写」
7. 观察是否使用阶跃星辰生成内容

---

## 四、模型选择建议

### 4.1 按场景选择

| 使用场景 | 推荐模型 | 原因 |
|---------|---------|------|
| 短文本续写 | step-1-8k | 速度快，成本低 |
| 段落润色 | step-1-32k | 标准能力，性价比高 |
| 文献综述 | step-1-128k | 长文本支持 |
| 整篇论文分析 | step-1-256k | 超长上下文 |
| 高质量学术写作 | step-2-16k | 新一代模型，质量更好 |
| 大规模文献对比 | step-2-200k | 超大上下文，可处理多篇文献 |

### 4.2 切换模型

修改 `.env` 文件中的模型配置：

```env
# 切换到长文本模型
STEPFUN_MODEL=step-1-128k

# 切换到新一代模型
STEPFUN_MODEL=step-2-16k
```

重启服务后生效。

---

## 五、故障排查

### 5.1 常见问题

#### 问题1：API Key 无效

**现象**：
```json
{
  "code": 401,
  "message": "调用阶跃星辰 API 失败: 401 Unauthorized"
}
```

**解决方案**：
1. 检查 API Key 是否复制完整（以 `step-` 开头）
2. 确认 API Key 没有多余的空格
3. 在阶跃星辰控制台确认应用状态为「正常」
4. 重新生成 API Key 并更新配置

#### 问题2：模型未开通

**现象**：
```json
{
  "code": 403,
  "message": "模型 step-2-16k 未开通权限"
}
```

**解决方案**：
1. 登录阶跃星辰控制台
2. 进入「应用管理」→「模型权限」
3. 申请开通对应模型
4. 或切换为已开通的模型（如 step-1-8k）

#### 问题3：网络连接失败

**现象**：
```json
{
  "code": 503,
  "message": "调用阶跃星辰 API 失败: ConnectTimeout"
}
```

**解决方案**：
1. 检查网络连接是否正常
2. 确认能访问 https://api.stepfun.com
3. 如果使用代理，配置 HTTP_PROXY 环境变量
4. 切换为其他AI提供商（如 DeepSeek）

#### 问题4：余额不足

**现象**：
```json
{
  "code": 402,
  "message": "账户余额不足"
}
```

**解决方案**：
1. 登录阶跃星辰控制台
2. 进入「财务管理」→「充值」
3. 充值后可继续使用

### 5.2 查看日志

后端服务日志会显示使用的AI提供商：

```bash
# 启动时查看日志
python run.py ai

# 预期输出
INFO:     阶跃星辰(stepfun)服务初始化成功
INFO:     支持模型: ['step-1-8k', 'step-1-32k', ...]
```

### 5.3 调试模式

在 `.env` 中启用调试：

```env
DEBUG=true
```

重新启动服务，查看详细请求日志。

---

## 六、多AI提供商配置

### 6.1 配置多个提供商

```env
# 国际
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx

# 国产
DEEPSEEK_API_KEY=sk-xxxxxxxx
MOONSHOT_API_KEY=sk-xxxxxxxx
STEPFUN_API_KEY=step-xxxxxxxx

# 默认使用阶跃星辰
AI_DEFAULT_PROVIDER=stepfun

# 启用故障转移（主服务失败时自动切换）
AI_FALLBACK_ENABLED=true
```

### 6.2 故障转移顺序

当 `AI_FALLBACK_ENABLED=true` 时：
1. 先尝试 `AI_DEFAULT_PROVIDER` 指定的提供商
2. 失败后自动切换到其他可用提供商
3. 所有提供商都失败时返回模拟响应

---

## 七、费用说明

### 7.1 阶跃星辰定价（参考）

| 模型 | 输入价格 | 输出价格 |
|-----|---------|---------|
| step-1-8k | ¥0.001/1K tokens | ¥0.002/1K tokens |
| step-1-32k | ¥0.002/1K tokens | ¥0.004/1K tokens |
| step-1-128k | ¥0.004/1K tokens | ¥0.008/1K tokens |
| step-1-256k | ¥0.008/1K tokens | ¥0.016/1K tokens |
| step-2-16k | ¥0.003/1K tokens | ¥0.006/1K tokens |
| step-2-200k | ¥0.006/1K tokens | ¥0.012/1K tokens |

> 价格可能有变动，以官网实际价格为准：https://platform.stepfun.com/pricing

### 7.2 费用估算

在ScholarForge中查看Token使用量：

```bash
# 查看AI服务使用统计
curl http://localhost:8000/api/v1/ai/usage
```

响应示例：
```json
{
  "code": 200,
  "data": {
    "providers": {
      "stepfun": {
        "tokens": {
          "prompt": 15000,
          "completion": 5000,
          "total": 20000
        },
        "cost_usd": 0.08
      }
    }
  }
}
```

---

## 八、最佳实践

### 8.1 开发环境
- 使用 `step-1-8k` 模型，成本低，响应快
- 配置多个AI提供商作为备份

### 8.2 生产环境
- 使用 `step-2-16k` 模型，质量更好
- 单独配置 `.env` 文件，不提交到版本控制
- 定期查看Token使用量，控制成本

### 8.3 安全建议
1. **不要将 API Key 提交到 Git**
   ```bash
   # 确保 .env 在 .gitignore 中
   echo ".env" >> .gitignore
   ```

2. **定期更换 API Key**
   - 在阶跃星辰控制台重新生成
   - 更新 `.env` 文件
   - 重启服务

3. **使用环境变量而非硬编码**
   - 推荐：`.env` 文件
   - 不推荐：直接写在代码中

---

## 九、相关链接

- 阶跃星辰开放平台：https://platform.stepfun.com/
- API文档：https://platform.stepfun.com/docs
- 定价页面：https://platform.stepfun.com/pricing
- 模型介绍：https://www.stepfun.com/

---

## 十、快速检查清单

配置完成后，确认以下事项：

- [ ] 已在阶跃星辰平台注册并完成实名认证
- [ ] 已创建应用并获取 API Key
- [ ] 已开通所需模型的使用权限
- [ ] 已在 `.env` 文件中正确配置 API Key
- [ ] 已设置 `AI_DEFAULT_PROVIDER=stepfun`（如需设为默认）
- [ ] 已重启后端服务
- [ ] 已通过健康检查接口验证配置
- [ ] 已在前端测试AI写作功能正常

---

**最后更新**：2026-03-04
**文档版本**：v1.0

如有问题，请检查后端服务日志或联系阶跃星辰客服。
