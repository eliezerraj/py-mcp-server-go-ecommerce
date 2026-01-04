import logging
import inspect
import aiohttp

from typing import Optional
from app.server.mcp_server import SESSION_TIMEOUT, INVENTORY_URL, mcp
from app.log.logger import REQUEST_ID_CTX

from opentelemetry import trace, propagate
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

session_timeout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)

# -----------------------------------------------------
# Inventory Heatlhy
# -----------------------------------------------------
@mcp.tool(name="inventory_healthy")
async def inventory_healthy(context: Optional[dict] = None) -> str:
    """
    Check the healthy status of Inventory service.
    
    Args:
        - context: JWT and some metadata
    Response:
        - content: all information about Inventory service healthy status and enviroment variables.
    Raises:
        - valueError: http status code.
    """
    print('\033[31m =.=.= \033[0m' * 15)

    func_name = inspect.currentframe().f_code.co_name
    
    logger.info(f"func:{func_name} : context: {context}")

    url = INVENTORY_URL + "/info"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error

        if context:
            token_pre_state = REQUEST_ID_CTX.set(context.get("x-request-id", "MCP_NOT_INFORMED"))

        headers = {"Authorization": f"Bearer {jwt_token}",
                   "X-Request-Id": REQUEST_ID_CTX.get(),
        }            

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
            REQUEST_ID_CTX.reset(token_pre_state)
            detach(token)    

#----------------------------
# Create inventory
#----------------------------
@mcp.tool(name="create_inventory")
async def create_inventory( sku: str,
                            type: str,
                            name: str,
                            status: str,
                            context: Optional[dict] = None) -> str:
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

    func_name = inspect.currentframe().f_code.co_name
    
    logger.info(f"func:{func_name}: inventory: {sku} : {type} : {name} : {status} : context: {context}")
                
    url = INVENTORY_URL + "/product"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        if context:
            token_pre_state = REQUEST_ID_CTX.set(context.get("x-request-id", "MCP_NOT_INFORMED"))

        headers = {"Authorization": f"Bearer {jwt_token}",
                   "X-Request-Id": REQUEST_ID_CTX.get(),
        } 

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
            REQUEST_ID_CTX.reset(token_pre_state)
            detach(token)

#----------------------------
# Get product
#----------------------------
@mcp.tool(name="get_product")
async def get_product(sku: str, 
                      context: Optional[dict] = None) -> str:
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
    
    func_name = inspect.currentframe().f_code.co_name
    logger.info(f"func:{func_name} : product:{sku} : context: {context}")

    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error

        if context:
            token_pre_state = REQUEST_ID_CTX.set(context.get("x-request-id", "MCP_NOT_INFORMED"))

        headers = {"Authorization": f"Bearer {jwt_token}",
                   "X-Request-Id": REQUEST_ID_CTX.get(),
        }   
        
        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:

                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
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
            REQUEST_ID_CTX.reset(token_pre_state)
            detach(token)
        
#----------------------------
# Get inventory
#----------------------------
@mcp.tool(name="get_inventory")
async def get_inventory(sku: str, 
                        context: Optional[dict] = None) -> str:
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

    func_name = inspect.currentframe().f_code.co_name

    logger.info(f"func:{func_name} : product:{sku} : context: {context}")
    
    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        if context:
           token_pre_state = REQUEST_ID_CTX.set(context.get("x-request-id", "MCP_NOT_INFORMED"))

        headers = {"Authorization": f"Bearer {jwt_token}",
                   "X-Request-Id": REQUEST_ID_CTX.get(),
        } 
    
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
            REQUEST_ID_CTX.reset(token_pre_state)
            detach(token)

#----------------------------
# Update inventory
#----------------------------
@mcp.tool(name="update_inventory")
async def update_inventory( sku: str,
                            available: int,
                            reserved: int,
                            sold: int,
                            context: Optional[dict] = None) -> str:
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

    func_name = inspect.currentframe().f_code.co_name

    logger.info(f"func:{func_name} : inventory: {sku} : {available} : {reserved} : {sold} : context: {context}")

    url = INVENTORY_URL + f"/inventory/product/{sku}"

    # extract the trace infos
    carrier= context.get("_trace", {}) if context else {}
    ctx = extract(carrier)
    token = attach(ctx)
               
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error("message_error")
            return message_error
    
        if context:
            token_pre_state = REQUEST_ID_CTX.set(context.get("x-request-id", "MCP_NOT_INFORMED"))

        headers = {"Authorization": f"Bearer {jwt_token}",
                   "X-Request-Id": REQUEST_ID_CTX.get(),
        }  
        
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
            REQUEST_ID_CTX.reset(token_pre_state)
            detach(token)