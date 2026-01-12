import logging
import inspect
from multiprocessing import context
import aiohttp

from typing import Optional
from app.server.mcp_server import SESSION_TIMEOUT, INVENTORY_URL, mcp
from app.log.logger import REQUEST_ID_CTX
from app.middleware.context_middleware import context_middleware, JWT_TOKEN

from opentelemetry import trace, propagate
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

session_timeout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)

# -----------------------------------------------------
# Inventory Heatlh
# -----------------------------------------------------
@mcp.tool(name="inventory_health")
@context_middleware(require_context=True,
                    required_scope="tool:health")
async def inventory_health(context: Optional[dict] = None) -> dict:
    """
    Check the health and enviroment variables of Inventory service.
    
    Args:
        - context: JWT and some metadata
    Response:
        - content: all information about Inventory service health and enviroment variables.
    Raises:
        - valueError: http status code.
    """
    print('\033[31m =.=.= \033[0m' * 15)

    func_name = inspect.currentframe().f_code.co_name
    
    logger.info(f"func:{func_name}")

    url = INVENTORY_URL + "/info"

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX and JWT_TOKEN is already set in the middleware
        headers = {"Authorization": f"Bearer {JWT_TOKEN}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
        }   

        try:  
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "inventory_health", 
                                "data": data}
                    else:
                        message_error = f"Failed to fetch inventory health, statuscode: {resp.status}"
                        logger.error(message_error)
                        return {"status": "error", 
                                "status_code": resp.status, 
                                "message": message_error,
                                "data": None}   
        except Exception as e:
                span.record_exception(e)
                logger.error(f"Exception : {e}")
                return {"status": "error", 
                        "status_code": 500, 
                        "message": str(e),
                        "data": None}

#----------------------------
# Create inventory
#----------------------------
@mcp.tool(name="create_inventory")
@context_middleware(require_context=True,
                    required_scope="tool:read")
async def create_inventory( sku: str,
                            type: str,
                            name: str,
                            status: str,
                            context: Optional[dict] = None) -> dict:
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

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # extract jwt
        jwt_token = context.get("jwt") if context else None
        if not jwt_token:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
            logger.error(message_error)
            return {"status": "error", 
                    "status_code": 403,
                    "message": message_error,
                    "data": None}
    
        # the REQUEST_ID_CTX and JWT_TOKEN is already set in the middleware
        headers = {"Authorization": f"Bearer {JWT_TOKEN}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
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
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "create_inventory", 
                                "data": data}
                    else:
                        message_error = f"Failed to create inventory {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return {"status": "error", 
                                "status_code": resp.status, 
                                "message": message_error,
                                "data": None}  
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return {"status": "error", 
                     "status_code": 500, 
                    "message": str(e),
                    "data": None}

#----------------------------
# Get product
#----------------------------
@mcp.tool(name="get_product")
@context_middleware(require_context=True,
                    required_scope="tool:read")
async def get_product(sku: str, 
                      context: Optional[dict] = None) -> dict:
    """
    Get only the product details such as sku, type, name.

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

    url = INVENTORY_URL + f"/product/{sku}"

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX and JWT_TOKEN is already set in the middleware
        headers = {"Authorization": f"Bearer {JWT_TOKEN}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
        }   

        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "get_product", 
                                "data": data}
                    else:
                        message_error = f"Failed to fetch product from {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return {"status": "error", 
                                "status_code": resp.status, 
                                "message": message_error,
                                "data": None}  
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return {"status": "error", 
                    "status_code": 500, 
                    "message": str(e),
                    "data": None}
    
#----------------------------
# Get inventory
#----------------------------
@mcp.tool(name="get_inventory")
@context_middleware(require_context=True,
                    required_scope="tool:read")
async def get_inventory(sku: str, 
                        context: Optional[dict] = None) -> dict:
    """
    Get the inventory details such as sku, type, name, quantity available, reserved and sold.
    This tool is used whenever a explicit inventory request is made for inventory information of a product.

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

    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX and JWT_TOKEN is already set in the middleware
        headers = {"Authorization": f"Bearer {JWT_TOKEN}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
        }   
    
        try:     
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    span.set_attribute("http.status_code", resp.status)

                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"data: {data}")
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "get_inventory", 
                                "data": data}
                    else:
                        message_error = f"Failed to fetch inventory from {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return {"status": "error", 
                                "status_code": resp.status, 
                                "message": message_error,
                                "data": None} 
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return {"status": "error", 
                        "status_code": 500, 
                        "message": str(e),
                        "data": None}

#----------------------------
# Update inventory
#----------------------------
@mcp.tool(name="update_inventory")
@context_middleware(require_context=True,
                    required_scope="tool:read")
async def update_inventory( sku: str,
                            available: int,
                            reserved: int,
                            sold: int,
                            context: Optional[dict] = None) -> dict:
    """
    Update a product inventory.

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
             
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX and JWT_TOKEN is already set in the middleware
        headers = {"Authorization": f"Bearer {JWT_TOKEN}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
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
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "update_inventory", 
                                "data": data}
                    else:
                        message_error = f"Failed to update inventory {sku}, statuscode: {resp.status}"
                        logger.error(message_error)
                        return {"status": "error", 
                                "status_code": resp.status, 
                                "message": message_error,
                                "data": None}  
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Exception : {e}")
            return {"status": "error", 
                        "status_code": 500, 
                        "message": str(e),
                        "data": None}
