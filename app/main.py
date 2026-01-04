import logging
from app.model.entity import Info
from app.server.mcp_server import VERSION, PORT, ACCOUNT ,HOST, SESSION_TIMEOUT, INVENTORY_URL,ORDER_URL ,LOG_LEVEL,APP_NAME,OTEL_EXPORTER_OTLP_ENDPOINT,LOG_GROUP, mcp

from app.log.logger import setup_logger
from app.tracing.tracer import setup_tracer

from opentelemetry import trace

#---------------------------------
# Configure logging
#---------------------------------
setup_logger(LOG_LEVEL, APP_NAME, OTEL_EXPORTER_OTLP_ENDPOINT, LOG_GROUP)
logger = logging.getLogger(__name__)

#---------------------------------
# Configure tracer
#---------------------------------
setup_tracer(APP_NAME, OTEL_EXPORTER_OTLP_ENDPOINT)
tracer = trace.get_tracer(__name__)

# -----------------------------------------------------
# Info
# -----------------------------------------------------
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

logger.info(f"info: {info}")

# ------------------------------------------------------------------- #
# Load tools
# ------------------------------------------------------------------- #
from app.tools.info import mcp_info, ping 
from app.tools.inventory import inventory_healthy, create_inventory, get_product, get_inventory, update_inventory
from app.tools.order import order_healthy, get_order, checkout_order, create_order
# ------------------------------------------------------------------- #
# Main
# ------------------------------------------------------------------- #
if __name__ == "__main__":
    logger.info(f"SERVER: {HOST}:{PORT}")

    mcp.run(transport="streamable-http")    