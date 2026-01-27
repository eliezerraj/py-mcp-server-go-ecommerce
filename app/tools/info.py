import logging
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any

from app.model.entity import Info
from app.server.mcp_server import VERSION, PORT, ACCOUNT ,HOST, SESSION_TIMEOUT, INVENTORY_URL,ORDER_URL ,LOG_LEVEL,APP_NAME,OTEL_EXPORTER_OTLP_ENDPOINT,LOG_GROUP, mcp
from app.middleware.context_middleware import context_middleware

logger = logging.getLogger(__name__)

# -----------------------------------------------------
# Health Check
# -----------------------------------------------------
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """
    A simple health check that returns a healthy status.
    For a liveness probe, it should only confirm the process is running.
    """
    logger.debug("func:health_check")

    return JSONResponse({"message": "true"})

# -----------------------------------------------------
# Info service
# -----------------------------------------------------
@mcp.custom_route("/info", methods=["GET"])
async def info(request):
    """
    A simple info check that returns a information.
    """
    logger.info("func:info")

    info_data = {
            "version": VERSION,
            "account": ACCOUNT,
            "app_name": APP_NAME,
            "host": HOST,
            "port": int(PORT),
            "session_timeout": int(SESSION_TIMEOUT),
            "product_url": INVENTORY_URL,
            "order_url": ORDER_URL,
            "log_level": LOG_LEVEL,
    }

    return JSONResponse(info_data)

# -----------------------------------------------------
# Ping
# -----------------------------------------------------
@mcp.tool(name="ping")
async def ping() -> dict:
    """
    Standard MCP handshake/health check method.
    """
    print('\033[31m =.=.= \033[0m' * 15)
    logger.info("func:ping")

    return {"status": "success", 
            "status_code": 200,
            "message": "pong",
            "data": None}

# -----------------------------------------------------
# Info Mcp
# -----------------------------------------------------
@mcp.tool(name="mcp_info")
@context_middleware(require_context=True,
                    required_scope="tool:info")
async def mcp_info(context: Optional[dict] = None) -> dict:
    """
    Information MCP server.
    """
    print('\033[31m =.=.= \033[0m' * 15)
    logger.info("func:mcp_info")

    info_data = {
            "version": VERSION,
            "account": ACCOUNT,
            "app_name": APP_NAME,
            "host": HOST,
            "port": int(PORT),
            "session_timeout": int(SESSION_TIMEOUT),
            "product_url": INVENTORY_URL,
            "order_url": ORDER_URL,
            "log_level": LOG_LEVEL,
    }

    return {"status": "success", 
            "status_code": 200,
            "message": "mcp_info",
            "data": info_data}
