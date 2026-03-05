"""
A2UI完整演示 - 使用真实LLM模型
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """启动A2UI演示服务"""
    import uvicorn
    from .config import default_config

    logger.info("=" * 60)
    logger.info("启动 A2UI Demo 服务 (真实LLM模式)")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"LLM模型: {default_config.llm.model}")
    logger.info(f"API地址: {default_config.llm.api_base}")
    logger.info("")
    logger.info("服务地址:")
    logger.info("  - Web界面: http://localhost:8000")
    logger.info("  - API文档: http://localhost:8000/docs")
    logger.info("  - 健康检查: http://localhost:8000/health")
    logger.info("")
    logger.info("可用的Agent:")
    logger.info("  - ai_assistant: AI智能助手 (真实LLM)")
    logger.info("  - weather: 天气查询服务")
    logger.info("  - calculator: 数学计算器")
    logger.info("  - coordinator: 任务协调器 (真实LLM)")
    logger.info("")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 60)

    uvicorn.run(
        "ai.a2ui.api_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
