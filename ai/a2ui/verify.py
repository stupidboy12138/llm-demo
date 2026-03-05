#!/usr/bin/env python
"""
A2UI验证脚本
检查所有组件是否正确安装和配置
"""
import sys
import importlib
from pathlib import Path


def check_imports():
    """检查必要的导入"""
    print("=" * 60)
    print("检查Python包依赖")
    print("=" * 60)

    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("aiohttp", "aiohttp"),
        ("pydantic", "Pydantic"),
    ]

    all_ok = True

    for package, name in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {name:20} - 已安装")
        except ImportError:
            print(f"❌ {name:20} - 未安装")
            all_ok = False

    return all_ok


def check_a2a_modules():
    """检查A2A模块"""
    print("\n" + "=" * 60)
    print("检查A2A协议模块")
    print("=" * 60)

    modules = [
        ("a2a.protocol", "A2A协议"),
        ("a2a.base_agent", "基础Agent"),
        ("a2a.message_broker", "消息代理"),
        ("a2a.agent_impl", "Agent实现"),
    ]

    all_ok = True

    for module, name in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {name:20} - 可用")
        except ImportError as e:
            print(f"❌ {name:20} - 不可用: {e}")
            all_ok = False

    return all_ok


def check_a2ui_files():
    """检查A2UI文件"""
    print("\n" + "=" * 60)
    print("检查A2UI文件结构")
    print("=" * 60)

    base_path = Path(__file__).parent

    files = [
        ("__init__.py", "包初始化"),
        ("web_agent.py", "WebAgent"),
        ("demo_agents.py", "示例Agents"),
        ("api_server.py", "API服务器"),
        ("demo.py", "Demo启动脚本"),
        ("test_client.py", "测试客户端"),
        ("examples.py", "示例集合"),
        ("config.py", "配置文件"),
        ("run.py", "运行脚本"),
        ("README.md", "文档"),
        ("QUICKSTART.md", "快速入门"),
        ("static/index.html", "Web界面"),
    ]

    all_ok = True

    for file, name in files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✅ {name:20} - 存在")
        else:
            print(f"❌ {name:20} - 缺失: {file}")
            all_ok = False

    return all_ok


def check_a2ui_imports():
    """检查A2UI模块导入"""
    print("\n" + "=" * 60)
    print("检查A2UI模块导入")
    print("=" * 60)

    modules = [
        ("ai.a2ui.web_agent", "WebAgent"),
        ("ai.a2ui.demo_agents", "示例Agents"),
        ("ai.a2ui.api_server", "API服务器"),
        ("ai.a2ui.config", "配置"),
    ]

    all_ok = True

    for module, name in modules:
        try:
            mod = importlib.import_module(module)
            print(f"✅ {name:20} - 可导入")
        except Exception as e:
            print(f"❌ {name:20} - 导入失败: {e}")
            all_ok = False

    return all_ok


def check_classes():
    """检查关键类"""
    print("\n" + "=" * 60)
    print("检查关键类和函数")
    print("=" * 60)

    checks = []

    try:
        from ai.a2ui.web_agent import WebAgent
        print("✅ WebAgent类          - 可用")
        checks.append(True)
    except Exception as e:
        print(f"❌ WebAgent类          - 不可用: {e}")
        checks.append(False)

    try:
        from ai.a2ui.demo_agents import (
            AIAssistantAgent,
            WeatherAgent,
            CalculatorAgent,
            TaskCoordinatorAgent
        )
        print("✅ Agent实现           - 可用")
        checks.append(True)
    except Exception as e:
        print(f"❌ Agent实现           - 不可用: {e}")
        checks.append(False)

    try:
        from ai.a2ui.api_server import app
        print("✅ FastAPI应用         - 可用")
        checks.append(True)
    except Exception as e:
        print(f"❌ FastAPI应用         - 不可用: {e}")
        checks.append(False)

    try:
        from ai.a2ui.config import Config, load_config
        print("✅ 配置模块            - 可用")
        checks.append(True)
    except Exception as e:
        print(f"❌ 配置模块            - 不可用: {e}")
        checks.append(False)

    return all(checks)


def print_usage_info():
    """打印使用信息"""
    print("\n" + "=" * 60)
    print("如何使用A2UI")
    print("=" * 60)
    print()
    print("1. 启动服务:")
    print("   python -m ai.a2ui.demo")
    print("   或")
    print("   python -m ai.a2ui.run")
    print()
    print("2. 访问界面:")
    print("   http://localhost:8000")
    print()
    print("3. 查看API文档:")
    print("   http://localhost:8000/docs")
    print()
    print("4. 运行测试:")
    print("   python -m ai.a2ui.test_client")
    print()
    print("5. 运行示例:")
    print("   python -m ai.a2ui.examples")
    print()
    print("6. 命令行聊天:")
    print("   python -m ai.a2ui.test_client chat")
    print()


def print_install_instructions():
    """打印安装指导"""
    print("\n" + "=" * 60)
    print("安装缺失的依赖")
    print("=" * 60)
    print()
    print("使用pip:")
    print("  pip install fastapi uvicorn aiohttp pydantic websockets")
    print()
    print("使用uv (推荐):")
    print("  uv sync")
    print()


def main():
    """主函数"""
    print("\n" + "🔍 A2UI 系统验证")
    print()

    results = []

    # 检查依赖
    results.append(("依赖包", check_imports()))

    # 检查A2A模块
    results.append(("A2A模块", check_a2a_modules()))

    # 检查文件
    results.append(("文件结构", check_a2ui_files()))

    # 检查导入
    results.append(("模块导入", check_a2ui_imports()))

    # 检查类
    results.append(("关键类", check_classes()))

    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20} - {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 所有检查通过！系统已就绪。")
        print_usage_info()
        return 0
    else:
        print("⚠️  部分检查失败，请检查上述错误。")
        print_install_instructions()
        return 1


if __name__ == "__main__":
    sys.exit(main())
