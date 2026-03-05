#!/usr/bin/env python
"""
A2UI快速启动脚本
"""
import sys
import subprocess
from pathlib import Path


def main():
    """主函数"""
    print("=" * 60)
    print("A2UI - Agent to UI Interface Demo")
    print("=" * 60)
    print()

    # 检查依赖
    try:
        import fastapi
        import uvicorn
        import aiohttp
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print()
        print("请先安装依赖:")
        print("  pip install fastapi uvicorn aiohttp websockets")
        print()
        print("或使用 uv:")
        print("  uv sync")
        sys.exit(1)

    print("✅ 依赖检查通过")
    print()

    # 选择运行模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("请选择运行模式:")
        print("  1. 启动服务器 (server)")
        print("  2. 测试客户端 (test)")
        print("  3. 命令行聊天 (chat)")
        print()
        choice = input("请输入选项 [1]: ").strip() or "1"

        mode_map = {
            "1": "server",
            "2": "test",
            "3": "chat"
        }
        mode = mode_map.get(choice, "server")

    print(f"运行模式: {mode}")
    print("-" * 60)
    print()

    if mode == "server":
        print("🚀 启动A2UI服务器...")
        print()
        print("服务地址:")
        print("  - Web界面: http://localhost:8000")
        print("  - API文档: http://localhost:8000/docs")
        print("  - 健康检查: http://localhost:8000/health")
        print()
        print("按 Ctrl+C 停止服务")
        print("-" * 60)
        print()

        # 启动服务器
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "ai.a2ui.api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])

    elif mode == "test":
        print("🧪 运行测试客户端...")
        print()
        subprocess.run([sys.executable, "-m", "ai.a2ui.test_client"])

    elif mode == "chat":
        print("💬 启动命令行聊天...")
        print()
        subprocess.run([sys.executable, "-m", "ai.a2ui.test_client", "chat"])

    else:
        print(f"❌ 未知模式: {mode}")
        print()
        print("可用模式: server, test, chat")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见!")
        sys.exit(0)
