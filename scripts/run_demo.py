#!/usr/bin/env python3
"""
演示启动脚本
启动HTTP服务器并打开演示文稿

Usage:
    python scripts/run_demo.py
"""

import http.server
import socketserver
import webbrowser
import threading
import time
from pathlib import Path

# 配置
PORT = 8765
DEMO_DIR = Path(__file__).parent.parent / "demo" / "presentation"


class DemoHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    def log_message(self, format, *args):
        """简化日志输出"""
        print(f"[Demo Server] {args[0]}")


def start_server():
    """启动HTTP服务器"""
    with socketserver.TCPServer(("", PORT), DemoHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"Demo server running at http://localhost:{PORT}")
        print(f"{'='*50}\n")
        httpd.serve_forever()


def main():
    print("""
╔══════════════════════════════════════════════════╗
║                                                  ║
║           ScholarForge Demo Launcher             ║
║                                                  ║
╚══════════════════════════════════════════════════╝
    """)

    # 检查演示文件是否存在
    slides_file = DEMO_DIR / "slides.html"
    if not slides_file.exists():
        print(f"Error: Demo file not found at {slides_file}")
        return

    # 在后台启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器启动
    time.sleep(1)

    # 打开浏览器
    demo_url = f"http://localhost:{PORT}/slides.html"
    print(f"Opening browser: {demo_url}\n")
    webbrowser.open(demo_url)

    print("""
演示控制说明:
  → 或 空格    : 下一页
  ←           : 上一页
  ESC         : 退出全屏
  F11         : 全屏切换

按 Ctrl+C 停止服务器
""")

    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down demo server...")


if __name__ == "__main__":
    main()
