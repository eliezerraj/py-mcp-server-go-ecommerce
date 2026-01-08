from functools import wraps
from multiprocessing import context
from typing import Optional, Dict, Any

from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract

from app.log.logger import REQUEST_ID_CTX

#global jwt_token
JWT_TOKEN = None

def context_middleware(require_context: bool = True):
    """
    MCP tool middleware:
    - validates context
    - attaches trace context
    - sets request id
    - guarantees cleanup
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            context: Optional[Dict[str, Any]] = kwargs.get("context")

            # ----------------------------
            # Context validation
            # ----------------------------
            if require_context and context is None:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": "No context provided, BAD REQUEST",
                    "data": None,
                }

            if context is not None and not isinstance(context, dict):
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": "Invalid context, BAD REQUEST",
                    "data": None,
                }

            # ----------------------------
            # Request ID
            # ----------------------------
            REQUEST_ID_CTX.set(context.get("x-request-id", "NOT_INFORMED_BY_AGENT"))

            # ----------------------------
            # Tracing
            # ----------------------------
            carrier = context.get("_trace", {}) if context else {}
            trace_ctx = extract(carrier)
            trace_token = attach(trace_ctx)

            # ----------------------------
            # Jwt
            # ----------------------------
            JWT_TOKEN = context.get("jwt") if context else None
            if not JWT_TOKEN:
                message_error = "No JWT provided, NOT AUTHORIZED, statuscode: 403"
                return {"status": "error", 
                        "status_code": 403,
                        "message": message_error,
                        "data": None}

            try:
                return await func(*args, **kwargs)
            finally:
                detach(trace_token)

        return wrapper

    return decorator
