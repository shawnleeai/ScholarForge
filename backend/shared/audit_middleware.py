"""
审计日志中间件
记录所有请求用于安全审计和异常检测
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message

logger = logging.getLogger("audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件
    记录所有请求的详细信息用于安全审计
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[set] = None,
        sensitive_headers: Optional[set] = None,
        sensitive_body_patterns: Optional[set] = None,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
        }
        self.sensitive_headers = sensitive_headers or {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-auth-token",
        }
        self.sensitive_body_patterns = sensitive_body_patterns or {
            "password",
            "secret",
            "token",
            "credential",
            "api_key",
            "apikey",
        }

    def _mask_sensitive_data(self, data: dict) -> dict:
        """遮蔽敏感数据"""
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in self.sensitive_body_patterns):
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            elif isinstance(value, str) and len(value) > 100:
                masked[key] = value[:50] + "..." + value[-20:]
            else:
                masked[key] = value
        return masked

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _should_log_body(self, request: Request) -> bool:
        """判断是否应该记录请求体"""
        content_type = request.headers.get("content-type", "")
        # 只记录 JSON 和表单数据
        return any(
            ct in content_type
            for ct in ["application/json", "application/x-www-form-urlencoded"]
        )

    async def _get_request_body(self, request: Request) -> Optional[dict]:
        """安全地获取请求体"""
        try:
            if not self._should_log_body(request):
                return None

            body = await request.body()
            if not body:
                return None

            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                try:
                    data = json.loads(body.decode("utf-8"))
                    return self._mask_sensitive_data(data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return {"_raw": "<binary or invalid utf-8>"}

            elif "application/x-www-form-urlencoded" in content_type:
                # 表单数据
                return {"_form": "<form data>"}

            return None
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录审计日志"""
        # 跳过不需要记录的路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 开始计时
        start_time = time.time()

        # 收集请求信息
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # 获取请求头（遮蔽敏感信息）
        headers = {}
        for key, value in request.headers.items():
            if key.lower() in self.sensitive_headers:
                headers[key] = "***MASKED***"
            else:
                headers[key] = value

        # 获取请求体
        request_body = await self._get_request_body(request)

        # 获取用户 ID（如果已认证）
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # 提取 token 的一部分作为标识
            token = auth_header[7:]
            if len(token) > 20:
                user_id = f"token:{hashlib.sha256(token.encode()).hexdigest()[:16]}"

        # 执行请求
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            raise
        finally:
            # 计算处理时间
            process_time_ms = int((time.time() - start_time) * 1000)

            # 构建审计日志
            audit_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "query_params": query_params if query_params else None,
                "user_id": user_id,
                "status_code": response.status_code if response else 500,
                "process_time_ms": process_time_ms,
                "request_size": int(request.headers.get("content-length", 0)),
                "response_size": (
                    int(response.headers.get("content-length", 0))
                    if response
                    else 0
                ),
                "user_agent": request.headers.get("user-agent", ""),
                "error": error,
            }

            # 记录请求体（仅对敏感操作）
            if request_body and method in ["POST", "PUT", "PATCH", "DELETE"]:
                audit_log["request_body"] = request_body

            # 记录到日志
            if error:
                logger.error(f"AUDIT: {json.dumps(audit_log)}")
            elif response and response.status_code >= 400:
                logger.warning(f"AUDIT: {json.dumps(audit_log)}")
            else:
                logger.info(f"AUDIT: {json.dumps(audit_log)}")

        return response


def setup_audit_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
) -> None:
    """
    配置审计日志

    Args:
        log_file: 日志文件路径（如果为 None，只输出到控制台）
        log_level: 日志级别
    """
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(log_level)

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    audit_logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        audit_logger.addHandler(file_handler)


# 检测异常行为的辅助函数
def detect_anomalous_patterns(requests: list[dict]) -> list[dict]:
    """
    检测异常请求模式

    Args:
        requests: 请求日志列表

    Returns:
        list: 检测到的异常列表
    """
    anomalies = []

    # 按 IP 分组
    ip_counts: dict[str, int] = {}
    for req in requests:
        ip = req.get("client_ip", "unknown")
        ip_counts[ip] = ip_counts.get(ip, 0) + 1

    # 检测高频请求
    for ip, count in ip_counts.items():
        if count > 100:  # 每分钟超过100次请求
            anomalies.append({
                "type": "high_frequency",
                "ip": ip,
                "count": count,
                "message": f"IP {ip} 发起了 {count} 次请求",
            })

    # 检测失败的认证尝试
    failed_auth = [
        req for req in requests
        if req.get("path", "").endswith("/auth/login")
        and req.get("status_code") == 401
    ]

    if len(failed_auth) > 5:
        ips = set(req.get("client_ip") for req in failed_auth)
        anomalies.append({
            "type": "failed_auth_attempts",
            "count": len(failed_auth),
            "ips": list(ips),
            "message": f"检测到 {len(failed_auth)} 次失败的登录尝试",
        })

    return anomalies
