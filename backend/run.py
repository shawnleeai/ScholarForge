#!/usr/bin/env python3
"""
ScholarForge Backend Runner
统一启动脚本 - 支持启动单个或所有微服务
"""

import asyncio
import argparse
import subprocess
import sys
import os
from pathlib import Path

# 服务配置
SERVICES = {
    "gateway": {
        "port": 8000,
        "module": "gateway.main:app",
        "description": "API网关（统一入口）",
    },
    "user": {
        "port": 8001,
        "module": "services.user.main:app",
        "description": "用户认证与管理服务",
    },
    "article": {
        "port": 8002,
        "module": "services.article.main:app",
        "description": "文献检索与管理服务",
    },
    "paper": {
        "port": 8003,
        "module": "services.paper.main:app",
        "description": "论文编辑与管理服务",
    },
    "ai": {
        "port": 8004,
        "module": "services.ai.main:app",
        "description": "AI写作助手服务",
    },
    "recommendation": {
        "port": 8005,
        "module": "services.recommendation.main:app",
        "description": "推荐服务",
    },
    "collaboration": {
        "port": 8006,
        "module": "services.collaboration.main:app",
        "description": "实时协作服务",
    },
    "annotation": {
        "port": 8007,
        "module": "services.annotation.main:app",
        "description": "批注/评论服务",
    },
    "journal": {
        "port": 8008,
        "module": "services.journal.main:app",
        "description": "期刊智能匹配服务",
    },
    "plagiarism": {
        "port": 8009,
        "module": "services.plagiarism.main:app",
        "description": "查重检测服务",
    },
    "topic": {
        "port": 8010,
        "module": "services.topic.main:app",
        "description": "智能选题助手服务",
    },
    "knowledge": {
        "port": 8011,
        "module": "services.knowledge.main:app",
        "description": "知识图谱服务",
    },
    "progress": {
        "port": 8012,
        "module": "services.progress.main:app",
        "description": "进度管理服务",
    },
}


def run_service(service_name: str, port: int, reload: bool = True):
    """启动单个服务"""
    service = SERVICES.get(service_name)
    if not service:
        print(f"错误: 未知服务 '{service_name}'")
        print(f"可用服务: {', '.join(SERVICES.keys())}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "uvicorn",
        service["module"],
        "--host", "0.0.0.0",
        "--port", str(port or service["port"]),
    ]
    if reload:
        cmd.append("--reload")

    print(f"启动服务: {service_name} ({service['description']})")
    print(f"地址: http://localhost:{port or service['port']}")
    print(f"文档: http://localhost:{port or service['port']}/docs")
    print("-" * 50)

    subprocess.run(cmd)


def run_all_services(include_gateway: bool = True):
    """启动所有服务（使用不同进程）"""
    processes = []

    # 过滤掉网关（如果不需要）
    services_to_start = {k: v for k, v in SERVICES.items() if include_gateway or k != "gateway"}

    for name, config in services_to_start.items():
        cmd = [
            sys.executable, "-m", "uvicorn",
            config["module"],
            "--host", "0.0.0.0",
            "--port", str(config["port"]),
        ]
        print(f"启动 {name} 服务于端口 {config['port']}...")
        proc = subprocess.Popen(cmd)
        processes.append((name, proc))

    print("\n" + "=" * 50)
    print("所有服务已启动:")
    for name, config in services_to_start.items():
        print(f"  {name}: http://localhost:{config['port']}")
    print("=" * 50)
    print("\n前端连接:")
    print(f"  API网关: http://localhost:8000")
    print(f"  前端开发服务器: http://localhost:3000")
    print("\n按 Ctrl+C 停止所有服务")

    try:
        # 等待所有进程
        for name, proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止所有服务...")
        for name, proc in processes:
            proc.terminate()
        print("所有服务已停止")


def run_dev():
    """开发模式：启动网关和用户服务（最小化启动）"""
    processes = []

    # 开发模式只启动核心服务
    dev_services = ["gateway", "user"]

    for name in dev_services:
        config = SERVICES[name]
        cmd = [
            sys.executable, "-m", "uvicorn",
            config["module"],
            "--host", "0.0.0.0",
            "--port", str(config["port"]),
            "--reload",
        ]
        print(f"启动 {name} 服务于端口 {config['port']}...")
        proc = subprocess.Popen(cmd)
        processes.append((name, proc))

    print("\n" + "=" * 50)
    print("开发模式 - 已启动服务:")
    for name in dev_services:
        config = SERVICES[name]
        print(f"  {name}: http://localhost:{config['port']}")
    print("=" * 50)
    print("\n前端连接:")
    print(f"  前端开发服务器: http://localhost:3000")
    print("\n按 Ctrl+C 停止所有服务")

    try:
        for name, proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止所有服务...")
        for name, proc in processes:
            proc.terminate()
        print("所有服务已停止")


def init_database():
    """初始化数据库"""
    print("初始化数据库...")
    from shared.database import init_db, engine
    from services.user.models import User, Team, TeamMember

    async def _init():
        async with engine.begin() as conn:
            # 导入所有模型
            from services.article.models import Article, ArticleCollection
            from services.paper.models import Paper, PaperSection

            # 创建所有表
            from shared.database import Base
            await conn.run_sync(Base.metadata.create_all)

        print("数据库表创建成功!")

    asyncio.run(_init())


def main():
    parser = argparse.ArgumentParser(
        description="ScholarForge Backend Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py user              # 启动用户服务
  python run.py user --port 9001  # 指定端口启动
  python run.py all               # 启动所有服务（包括网关）
  python run.py dev               # 开发模式（网关+用户服务）
  python run.py gateway           # 只启动API网关
  python run.py init-db           # 初始化数据库
  python run.py --list            # 列出所有服务
        """
    )

    parser.add_argument(
        "service",
        nargs="?",
        default="user",
        help="要启动的服务名称 (默认: user)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="指定服务端口"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="禁用热重载"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用服务"
    )

    args = parser.parse_args()

    if args.list:
        print("可用服务:")
        print("-" * 50)
        for name, config in SERVICES.items():
            print(f"  {name:15} - {config['description']} (端口: {config['port']})")
        return

    if args.service == "all":
        run_all_services()
    elif args.service == "dev":
        run_dev()
    elif args.service == "init-db":
        init_database()
    else:
        run_service(args.service, args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
