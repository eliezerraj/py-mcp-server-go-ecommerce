import logging
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from functools import wraps
from multiprocessing import context
from typing import Optional, Dict, Any

from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract

from app.log.logger import REQUEST_ID_CTX

from app.server.mcp_server import mcp

logger = logging.getLogger(__name__)

#global jwt_token
JWT_TOKEN = None
ALGORITHM = "RS256"

# ---------------------
# Load the PubKey
# ---------------------
def load_public_key():
    logger.info("func:load_public_key")
    with open("./assets/certs/server-public.key", "r") as f:
        return f.read()

def error_response(status_code: int, message: str):
    return {
        "status": "error",
        "status_code": status_code,
        "message": message,
        "data": None,
    }

class ContextError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)

PUBLIC_KEY = load_public_key()

def context_middleware(require_context: bool = True,
                       required_scope: str | None = None):
    """
    MCP tool middleware:
    - validates context
    - attaches trace context
    - sets request id
    - validate jwt
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
                raise ContextError(400, "No context provided, BAD REQUEST")

            if context is not None and not isinstance(context, dict):
                raise ContextError(400, "Invalid context, BAD REQUEST")

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
            JWT_TOKEN = context.get("Authorization") if context else None
            if not JWT_TOKEN:
                raise ContextError(403, "No JWT provided, NOT AUTHORIZED")

            try:
                decoded_claims = jwt.decode(
                    JWT_TOKEN,
                    PUBLIC_KEY,
                    algorithms=[ALGORITHM],
                )

                print("Decoded Claims:", decoded_claims)
                scopes = decoded_claims.get("scope", [])

                if not isinstance(scopes, list):
                    raise ContextError(403, "Scope malformed")
                
                if required_scope:
                    if "admin" not in scopes and required_scope not in scopes:
                        raise ContextError(403, "Insufficient scope")
                                            
                return await func(*args, **kwargs)
            
            except ExpiredSignatureError:
                return error_response(401, "Token has expired")
            except InvalidTokenError as e:
                return error_response(401, f"Invalid token: {e}")
            except ContextError as e:
                return error_response(e.status_code, e.message)
            except Exception as e:
                return error_response(500, e.message)
            finally:
                if trace_token is not None:
                    detach(trace_token)

        return wrapper
    return decorator
