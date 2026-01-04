import logging
from fastapi.responses import JSONResponse

from app.model.entity import Info
from app.server.mcp_server import VERSION, PORT, ACCOUNT ,HOST, SESSION_TIMEOUT, INVENTORY_URL,ORDER_URL ,LOG_LEVEL,APP_NAME,OTEL_EXPORTER_OTLP_ENDPOINT,LOG_GROUP, mcp

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
    logger.info("func:health_check")

    return JSONResponse({"message": "true"})

# -----------------------------------------------------
# Ping
# -----------------------------------------------------
@mcp.tool(name="ping")
async def ping() -> str:
    """
    Standard MCP handshake/health check method.
    """
    print('\033[31m =.=.= \033[0m' * 15)
    logger.info("func:ping")

    return "pong"

# -----------------------------------------------------
# Info
# -----------------------------------------------------
@mcp.tool(name="mcp_info")
async def mcp_info() -> str:
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

    # Initialize with a default value
    info = ""

    try:
        info_obj = Info(**info_data)
        info = info_obj.model_dump_json()
    except Exception as e:
        logger.error(f"Exception : {e}")

    return info
