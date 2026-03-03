#!/usr/bin/env python3
"""
集成测试脚本
测试所有服务的健康状态和API可用性
"""

import asyncio
import sys
import httpx
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ServiceCheck:
    name: str
    url: str
    status: str = "unknown"
    response_time: float = 0.0
    error: str = ""


SERVICES = [
    ServiceCheck("API Gateway", "http://localhost:8000/health"),
    ServiceCheck("User Service", "http://localhost:8001/health"),
    ServiceCheck("Article Service", "http://localhost:8002/health"),
    ServiceCheck("Paper Service", "http://localhost:8003/health"),
    ServiceCheck("AI Service", "http://localhost:8004/health"),
    ServiceCheck("Recommendation Service", "http://localhost:8005/health"),
]

API_ENDPOINTS = [
    ("GET", "/api/v1/papers", "论文列表"),
    ("GET", "/api/v1/topic/suggestions", "选题建议"),
    ("GET", "/api/v1/progress/milestones", "进度里程碑"),
    ("GET", "/api/v1/journal/matches", "期刊匹配"),
    ("GET", "/api/v1/knowledge/graph", "知识图谱"),
    ("GET", "/api/v1/reference/papers", "参考文献"),
    ("GET", "/api/v1/plagiarism/engines", "查重引擎"),
    ("GET", "/api/v1/format/templates", "格式模板"),
    ("GET", "/api/v1/defense/checklist/mock-id", "答辩清单"),
]


async def check_service_health(service: ServiceCheck) -> ServiceCheck:
    """检查单个服务健康状态"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            import time
            start = time.time()
            response = await client.get(service.url)
            elapsed = time.time() - start

            service.response_time = round(elapsed * 1000, 2)  # ms

            if response.status_code == 200:
                data = response.json()
                service.status = data.get("status", "unknown")
            else:
                service.status = "error"
                service.error = f"HTTP {response.status_code}"

        except httpx.ConnectError:
            service.status = "offline"
            service.error = "Connection refused"
        except httpx.TimeoutException:
            service.status = "timeout"
            service.error = "Request timeout"
        except Exception as e:
            service.status = "error"
            service.error = str(e)

    return service


async def check_api_endpoints(base_url: str = "http://localhost:8000") -> List[Tuple[str, str, bool, str]]:
    """检查API端点"""
    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for method, endpoint, name in API_ENDPOINTS:
            try:
                url = f"{base_url}{endpoint}"
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url)

                # 200-299 或 401（需要认证）都算正常
                is_ok = 200 <= response.status_code < 300 or response.status_code == 401
                status = "✓" if is_ok else f"✗ ({response.status_code})"
                results.append((name, endpoint, is_ok, status))

            except Exception as e:
                results.append((name, endpoint, False, f"✗ ({str(e)[:30]})"))

    return results


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_results(services: List[ServiceCheck]):
    """打印服务检查结果"""
    print_header("Service Health Check")

    for service in services:
        status_icon = "✓" if service.status == "healthy" else "✗"
        status_color = "\033[92m" if service.status == "healthy" else "\033[91m"
        reset = "\033[0m"

        print(f"{status_color}{status_icon}{reset} {service.name:25} ", end="")

        if service.status == "healthy":
            print(f"[{service.status}] ({service.response_time}ms)")
        else:
            print(f"[{service.status}] {service.error}")

    # 统计
    healthy_count = sum(1 for s in services if s.status == "healthy")
    print(f"\nTotal: {healthy_count}/{len(services)} services healthy")


def print_api_results(results: List[Tuple[str, str, bool, str]]):
    """打印API检查结果"""
    print_header("API Endpoint Check")

    for name, endpoint, is_ok, status in results:
        status_icon = "✓" if is_ok else "✗"
        status_color = "\033[92m" if is_ok else "\033[91m"
        reset = "\033[0m"

        print(f"{status_color}{status_icon}{reset} {name:20} {endpoint:30} {status}")

    ok_count = sum(1 for _, _, is_ok, _ in results if is_ok)
    print(f"\nTotal: {ok_count}/{len(results)} endpoints OK")


def print_summary(services: List[ServiceCheck], api_results: List[Tuple[str, str, bool, str]]):
    """打印总结"""
    print_header("Summary")

    healthy_services = sum(1 for s in services if s.status == "healthy")
    ok_apis = sum(1 for _, _, is_ok, _ in api_results if is_ok)

    total_score = ((healthy_services + ok_apis) / (len(services) + len(api_results))) * 100

    print(f"Services Healthy: {healthy_services}/{len(services)}")
    print(f"APIs Available:   {ok_apis}/{len(api_results)}")
    print(f"Overall Score:    {total_score:.1f}%")

    if total_score >= 90:
        print("\n\033[92m✓ All systems operational\033[0m")
    elif total_score >= 70:
        print("\n\033[93m⚠ Some services degraded\033[0m")
    else:
        print("\n\033[91m✗ Critical issues detected\033[0m")


async def main():
    """主函数"""
    print("ScholarForge Integration Test")
    print("=" * 60)

    # 检查服务健康
    service_tasks = [check_service_health(s) for s in SERVICES]
    services = await asyncio.gather(*service_tasks)
    print_results(services)

    # 检查API端点
    api_results = await check_api_endpoints()
    print_api_results(api_results)

    # 打印总结
    print_summary(services, api_results)

    # 返回退出码
    healthy_count = sum(1 for s in services if s.status == "healthy")
    return 0 if healthy_count == len(SERVICES) else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        sys.exit(1)
