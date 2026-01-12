import os
from mcp.server.fastmcp import FastMCP

#---------------------------------
# Initialize tracing
#---------------------------------
VERSION = os.getenv("VERSION")
ACCOUNT = os.getenv("ACCOUNT")
APP_NAME = os.getenv("APP_NAME")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT")) 
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
INVENTORY_URL = os.getenv("INVENTORY_URL") 
ORDER_URL = os.getenv("ORDER_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
OTEL_STDOUT_LOG_GROUP = os.getenv("OTEL_STDOUT_LOG_GROUP", "false").lower() == "true"
LOG_GROUP = os.getenv("LOG_GROUP")

print("---" * 15)
print(f"VERSION: {VERSION}")
print(f"ACCOUNT: {ACCOUNT}")
print(f"APP_NAME: {APP_NAME}")

print(f"INVENTORY_URL: {INVENTORY_URL}")
print(f"ORDER_URL: {ORDER_URL}")

print(f"HOST: {HOST}")
print(f"PORT: {PORT}")
print(f"SESSION_TIMEOUT: {SESSION_TIMEOUT}")
print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {OTEL_EXPORTER_OTLP_ENDPOINT}")
print(f"LOG_LEVEL: {LOG_LEVEL}")
print(f"OTEL_STDOUT_LOG_GROUP: {OTEL_STDOUT_LOG_GROUP}")
print(f"LOG_GROUP: {LOG_GROUP}")
print("CWD:", os.getcwd())
print("---" * 15)

#---------------------------------
# setup MCP server
#---------------------------------
mcp = FastMCP(name=APP_NAME,        
              host=HOST,
              port=PORT,
              debug=True,
)