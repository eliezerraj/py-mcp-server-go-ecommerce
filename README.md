## py-mcp-server-go-ecommerce

Custom MCP server for POC purposes.

The MCP expose/access the public endpoints for go-inventory and go-order using python FASTAPI.

## Integration

   This is workload requires go-inventory and go-order

   The integrations are made via http-streamable api request.

## Enviroment variables

To run in local machine for local tests creat a .env in /cmd folder

    VERSION=1.0.0
    ACCOUNT=aws:999999999
    APP_NAME=py-mcp-server-ecommerce.localhost
    HOST=127.0.0.1 
    PORT=9002
    SESSION_TIMEOUT=700
    OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
    INVENTORY_URL=http://localhost:7000
    ORDER_URL=http://localhost:7004
    LOG_LEVEL=INFO 
    OTEL_STDOUT_LOG_GROUP=True
    LOG_GROUP=/mnt/c/Eliezer/log/py-mcp-server-go-ecommerce.log

## create venv

    python3 -m venv .venv

## activate

    source .venv/bin/activate

## install dependecies

    pip install -r requirements.txt

## run (root)

    python -m app.main

## test Local

    export VERSION=0.1
    export ACCOUNT=aws:999999999
    export APP_NAME=py-mcp-server-go-ecommerce.localhost
    export HOST=127.0.0.1 
    export PORT=9002
    export SESSION_TIMEOUT=700
    export OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
    export INVENTORY_URL=http://localhost:7000
    export INVENTORY_URL=https://go-api-global.architecture.caradhras.io/inventory
    export ORDER_URL=http://localhost:7004
    export ORDER_URL=https://go-api-global.architecture.caradhras.io/order
    export LOG_LEVEL=INFO 
    export OTEL_STDOUT_LOG_GROUP=True
    export LOG_GROUP=/mnt/c/Eliezer/log/py-mcp-server-go-ecommerce.log

## forward otel traces/metrics

    kubectl port-forward svc/arch-eks-01-02-otel-collector 4317:4317

## run mcp inspector

    Session 1 (venv activated and NO EXPORT env)
    npx @modelcontextprotocol/inspector 

    Sesssion 2 (venv activated)
    python -m app.main

    Setup
    Transport Type: streamable http
    URL: http://localhost:9002/mcp

## context

        {
        "Authorization": "eyJhbGci......72QMShTm9Vf7JnJx2w",
        "x-request-id": "111122223333-4444-55555-66666"
        }

## 1 Session Open

    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -d '{   "jsonrpc":"2.0",
                "id":1,
                "method":"sessions/open",
                "params":{
                    "protocolVersion":"2025-06-18",
                    "capabilities":{"tools":{}},
                    "clientInfo":{  "name":"test-client", 
                                    "version":"1.0.0"
                    }
            }
        }' \
        -v 2>&1 | grep -i "mcp-session-id" | cut -d' ' -f3

export SESSION_ID=91b6eea6b2a948cca53ce3dfce277870

## 1 Initialize

    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -H "Mcp-Session-Id: $SESSION_ID" \
        -d '{   "jsonrpc":"2.0",
                "id":1,
                "method":"initialize",
                "params":{"protocolVersion":"2025-06-18",
                    "capabilities":{"tools":{}},
                    "clientInfo":{"name":"test-client",
                    "version":"1.0.0"}
                }
            }'

## 3. Send Initialized Notification

    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -H "Mcp-Session-Id: $SESSION_ID" \
        -d '{   "jsonrpc":"2.0",
                "method":"notifications/initialized"
        }'

## 4. List Tools

    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -H "Mcp-Session-Id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0",
            "id":1,
            "method":"tools/list"
        }'

## 5. Call Tool

    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -H "Mcp-Session-Id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0",
            "id":2,
            "method":"server_info",
            "params":{}
        }'

## 4. Call Tool
    curl -X POST http://localhost:9002/mcp \
        -H "Content-Type: application/json" \
        -H "MCP-Protocol-Version: 2025-06-18" \
        -H "Accept: application/json, text/event-stream" \
        -H "Mcp-Session-Id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0","id":3,"method":"inventory_healthy","params":{"context":{"jwt":"123456"}}}'
