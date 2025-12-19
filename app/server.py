import os
import logging
import aiohttp
from dotenv import load_dotenv
from datetime import datetime

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP

from opentelemetry import trace, metrics, propagate
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import inject
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach

# Load .env file
load_dotenv()

#---------------------------------
# Initialize tracing
#---------------------------------

POD_NAME = os.getenv("POD_NAME")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT")) 
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
#INVENTORY_URL = "https://go-api-global.architecture.caradhras.io/inventory"
INVENTORY_URL = "http://localhost:7000"

#ORDER_URL = "https://go-api-global.architecture.caradhras.io/order"
ORDER_URL = "http://localhost:7004"

print("---" * 15)
print(f"POD_NAME: {POD_NAME}")
print(f"HOST: {HOST}")
print(f"PORT: {PORT}")
print(f"SESSION_TIMEOUT: {SESSION_TIMEOUT}")
print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {OTEL_EXPORTER_OTLP_ENDPOINT}")

# Create a TracerProvider
resource = Resource.create({
                "service.name": POD_NAME
})

trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# # Configure OTLP exporter and export spans via grpc
otlp_exporter = OTLPSpanExporter(
    endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, 
    insecure=True
)

# Add processor
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Optional: metrics (disabled if not needed)
metrics.set_meter_provider(MeterProvider(resource=resource))

# Instrument aiohttp and logging
AioHttpClientInstrumentor().instrument()
LoggingInstrumentor().instrument(set_logging_format=True)

# create trace
tracer = trace.get_tracer(POD_NAME)

#---------------------------------
# setup MCP server
#---------------------------------
mcp = FastMCP(name="mcp_server-go-commerce",        
              host=HOST,
              port=PORT,
              debug=True,
)

session_timeout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)

#---------------------------------
# Configure logging
#---------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# truncate logging
class TruncatingFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', max_msg_length=100):
        super().__init__(fmt, datefmt, style)
        self.max_msg_length = max_msg_length

    def format(self, record):
        if len(record.msg) > self.max_msg_length:
            record.msg = record.msg[:self.max_msg_length] + "..."
        return super().format(record)

handler = logging.StreamHandler()
formatter = TruncatingFormatter('%(asctime)s - %(levelname)s - %(message)s', max_msg_length=250)

handler.setFormatter(formatter)
logger.addHandler(handler)

# -----------------------------------------------------
# Ping
# -----------------------------------------------------
@mcp.tool(name="ping")
async def ping() -> str:
    """
    Standard MCP handshake/health check method.
    """
    print('\033[31m =.=.= \033[0m' * 15)
    logger.info("function => ping() called.")

    return "pong"

# -----------------------------------------------------
# Inventory
# -----------------------------------------------------
@mcp.tool(name="inventory_healthy")
async def inventory_healthy(context: dict = None) -> str:
    """
    Check the healthy status of Inventory service.
    
    Args:
        - context: context with a jwt embedded.
        - context: JWT and some metadata
    Response:
        - content: all information about Inventory service healthy status and enviroment variables.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => inventory_healthy()")

    url = INVENTORY_URL + "/info"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("inventory_healthy") as span:
        span.set_attribute("mcp.tool", "inventory_healthy")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
        
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}                  

        try:  
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:

                    span.set_attribute("http.status_code", resp.status)
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to fetch inventory healthy, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
                span.record_exception(e)
                logger.error(f"Exception : {e}")
                return {"status": "error", "reason": str(e), "status_code": 500}
        finally:
            detach(token)    

#----------------------------
@mcp.tool(name="create_inventory")
async def create_inventory( sku: str,
                            type: str,
                            name: str,
                            status: str,
                            context: dict = None) -> str:
    """
    Create a Inventory.

    Args:
        - sku: An Inventory sku id.
        - type: Inventory category type, ex: healt_care, foof, beverage, etc      
        - name: Inventory product name.
        - status: Inventory producte stock status, ex: IN-STOCK, OUT-OF-STOCK
        - context: JWT and some metadata
    Response:
        - product: a product created. 
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => create_inventory() = inventory: {sku} : {type} : {name} : {status}")
                
    url = INVENTORY_URL + "/product"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("create_inventory") as span:
        span.set_attribute("mcp.tool", "create_inventory")
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}   

        #prepare payload
        payload = {
            "sku": sku,
            "type": type,
            "name": name,
            "status": status
        }

        try:        
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to create inventory {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

#----------------------------
@mcp.tool(name="get_product")
async def get_product(sku: str, 
                      context: dict = None) -> str:
    """
    Get product details such as sku, type, name, status.

    Args:
        - product: Product Sku
        - context: JWT and some metadata
    Response:
        - product: all product information.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => get_product() = product:{sku}")
          
    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("get_product") as span:
        span.set_attribute("mcp.tool", "get_product")
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
        
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}   
        
        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:

                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to fetch product from {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)    
        
#----------------------------
@mcp.tool(name="get_inventory")
async def get_inventory(sku: str, 
                        context: dict = None) -> str:
    """
    Get the inventory details such as sku, type, name, status and quantity available, reserved and sold.

    Args:
        - product: Product Sku
        - context: context with a jwt embedded.
    Response:
        - inventory: all inventory information of a product.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => get_inventory() = product:{sku}")
    
    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("get_inventory") as span:
        span.set_attribute("mcp.tool", "get_inventory")
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"} 
    
        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:

                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to fetch inventory from {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

#----------------------------
@mcp.tool(name="update_inventory")
async def update_inventory( sku: str,
                            available: int,
                            reserved: int,
                            sold: int,
                            context: dict = None) -> str:
    """
    Create a inventory.

    Args:
        - sku: An inventory sku id.
        - available: Quantity of inventory product available.
        - reserved: Quantity of inventory product reserved.       
        - sold: Quantity of inventory product sold.
        - context: JWT and some metadata 
    Response:
        - inventory: the quantityties updated. 
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => update_inventory() = inventory: {sku} : {available} : {reserved} : {sold}")

    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)
               
    with tracer.start_as_current_span("update_inventory") as span:
        span.set_attribute("mcp.tool", "update_inventory")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}   
        
        payload = {
            "available": available,
            "reserved": reserved,
            "sold": sold
        }

        try:        
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.put(url, headers=headers, json=payload) as resp:
                   
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to update inventory {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

# -----------------------------------------------------
# order
# -----------------------------------------------------
@mcp.tool(name="order_healthy")
async def order_healthy(context: dict = None) -> str:
    """
    Check the healthy status of Order service.
    
    Args:
        - context: JWT and some metadata
    Response:
        - content: all information about Order service healthy status and enviroment variables.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => order_healthy()")

    url = ORDER_URL + "/info"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("order_healthy") as span:
        span.set_attribute("mcp.tool", "order_healthy")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}

        try: 
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:

                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        span.record_exception(e)
                        message_error = f"Failed to fetch order healthy, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

#----------------------------
@mcp.tool(name="get_order")
async def get_order(order: str, 
                    context: dict = None) -> str:
    """
    Get all order details details product details such as sku, type, name, status and quantity available, reserved and sold.

    Args:
        - order: order id
        - context: context with a jwt embedded.
    Response:
        - order: all order information.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => get_order() = order:{order}")

    url = ORDER_URL + f"/order/{order}"
    
    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("get_order") as span:
        span.set_attribute("mcp.tool", "get_order")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}   

        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to fetch order from {order}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

#----------------------------
@mcp.tool(name="checkout_order")
async def checkout_order(order: int,
                         payment: Dict[str, Any],
                         context: dict = None) -> str:
    """
    Do a checkout (payment) of a given order. A list of payments should be provided with data such as type (CASH, CREDIT or DEBIT), currency and amount.

    Args:
        - order: order id
        - payment: A list of payments methods. Each payment has type, currency and amount (numetic value)
        - context: context with a jwt embedded.
    Response:
        - order: all order information with his respective payments.
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => checkout_order() = order:{order} : {payment}")

    url = ORDER_URL + "/checkout"
    
    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("checkout_order") as span:
        span.set_attribute("mcp.tool", "checkout_order")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}   

        payload = {
                    "id": order,
                    "payment": [payment]
        }

        logger.info(f"payload: {payload}")

        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to fetch order from {order}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

#----------------------------
@mcp.tool(name="create_order")
async def create_order( user: str,
                        currency: str,
                        address: str,
                        cartItem: Dict[str, Any],
                        context: dict = None) -> str:
    """
    Create a order.

    Args:
        - user: An order user
        - currency: The order currency.
        - address: Shipping order address.       
        - cartItem: List of cart itens, with product with a sku, currency, quantity (numeric), price (numeric)
        - context: JWT and some metadata
    Response:
        - ordder: the order created. 
    Raises:
        - valueError: http status code.
    """

    print('\033[31m =.=.= \033[0m' * 15)
    logger.info(f"function => create_order() = order: {user} : {currency} : {address} : {cartItem}")

    url = ORDER_URL + "/order"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("mcp.tool", "create_order")
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        logger.info(f"jwt_token: {jwt_token}")
        headers = {"Authorization": f"Bearer {jwt_token}"}       

        transformed_cart_item = {
            "product": {
                "sku": cartItem.get("sku")
            },
            "currency": cartItem.get("currency"),
            "quantity": cartItem.get("quantity"),
            "price": cartItem.get("price")
        }

        payload = {
            "user_id": user,
            "currency": currency,
            "address": address,
            "cart": {
                "user_id": user,
                "cart_item": [transformed_cart_item],
            }
        }

        logger.info(f"payload: {payload}")           
        
        try:        
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        
                        span.set_attribute("http.status_code", resp.status)

                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return f"{data}"
                    else:
                        message_error = f"Failed to create ordder {user}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return message_error
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return f"Exception : {e}"
        finally:
            detach(token)

# ------------------------------------------------------------------- #
# Main
# ------------------------------------------------------------------- #
if __name__ == "__main__":
    print("-" * 45)
    print(f"CODE SERVER {HOST}:{PORT}")
    print("-" * 45)

    mcp.run(transport="streamable-http")    