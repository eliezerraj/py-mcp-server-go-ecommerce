import logging
import inspect
import aiohttp
from typing import Dict, Any

from typing import Optional
from app.log.logger import REQUEST_ID_CTX
from app.server.mcp_server import SESSION_TIMEOUT, ORDER_URL, mcp

from app.middleware.context_middleware import context_middleware

from opentelemetry import trace, propagate
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

session_timeout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)

# -----------------------------------------------------
# Order Health
# -----------------------------------------------------
@mcp.tool(name="order_health")
@context_middleware(require_context=True,
                    required_scope="tool:health")
async def order_health(context: Optional[dict] = None) -> dict:
    """
    Check the health and enviroment variables of Order service.
    
    Args:
        - context: JWT and some metadata
    Response:
        - content: all information about Order service health and enviroment variables.
    Raises:
        - valueError: http status code.
    """
    print('\033[31m =.=.= \033[0m' * 15)

    func_name = inspect.currentframe().f_code.co_name

    logger.info(f"func:{func_name}: context: {context}")

    url = ORDER_URL + "/info"
    
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX  is already set in the middleware
        headers = {"Authorization": f"Bearer {context.get('Authorization')}",
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
                                "message": "order_health", 
                                "data": data}
                    else:
                        span.record_exception(e)
                        message_error = f"Failed to fetch order health, statuscode: {resp.status}"
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

# -----------------------------------------------------
# Get Order
# -----------------------------------------------------
@mcp.tool(name="get_order")
@context_middleware(require_context=True,
                    required_scope="tool:get_order")
async def get_order(order: str, 
                    context: Optional[dict] = None) -> dict:
    """
    Get all order details details product details such as sku, type, name and quantity available, reserved and sold.

    Args:
        - order: order id
        - context: context with a jwt embedded.
    Response:
        - order: all order information.
    Raises:
        - valueError: http status code.
    """
    print('\033[31m =.=.= \033[0m' * 15)

    func_name = inspect.currentframe().f_code.co_name

    logger.info(f"func:{func_name} : order:{order} : context: {context}")

    url = ORDER_URL + f"/order/{order}"
        
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX  is already set in the middleware
        headers = {"Authorization": f"Bearer {context.get('Authorization')}",
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
                                "message": "get_order", 
                                "data": data}
                    else:
                        message_error = f"Failed to fetch order from {order}, statuscode: {resp.status}"
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

# -----------------------------------------------------
# Checkout Order
# -----------------------------------------------------
@mcp.tool(name="checkout_order")
@context_middleware(require_context=True,
                    required_scope="tool:checkout_order")
async def checkout_order(order: int,
                         payment: Dict[str, Any],
                         context: Optional[dict] = None) -> dict:
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

    func_name = inspect.currentframe().f_code.co_name

    logger.info(f"func:{func_name} : order:{order} : payment: {payment} : context: {context}")

    url = ORDER_URL + "/checkout"
    
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX  is already set in the middleware
        headers = {"Authorization": f"Bearer {context.get('Authorization')}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
        } 

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
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "checkout_order", 
                                "data": data}
                    else:
                        message_error = f"Failed to fetch order from {order}, statuscode: {resp.status}"
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

# -----------------------------------------------------
# Create Order
# -----------------------------------------------------
@mcp.tool(name="create_order")
@context_middleware(require_context=True,
                    required_scope="tool:create_order")
async def create_order( user: str,
                        currency: str,
                        address: str,
                        cartItem: Dict[str, Any],
                        context: Optional[dict] = None) -> dict:
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
    
    func_name = inspect.currentframe().f_code.co_name
    
    logger.info(f"func:{func_name} : order: {user} : {currency} : {address} : {cartItem} : context: {context}")

    url = ORDER_URL + "/order"
    
    with tracer.start_as_current_span(func_name) as span:
        span.set_attribute("mcp.tool", func_name)
        span.set_attribute("request.url", url) 

        # the REQUEST_ID_CTX  is already set in the middleware
        headers = {"Authorization": f"Bearer {context.get('Authorization')}",
                   "X-Request-Id": REQUEST_ID_CTX.get()
        }     

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
                        return {"status": "success", 
                                "status_code": resp.status,
                                "message": "create_order", 
                                "data": data}
                    else:
                        message_error = f"Failed to create ordder {user}, statuscode: {resp.status}"
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