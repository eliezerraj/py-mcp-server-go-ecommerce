#docker build -t py-mcp-server-go-commerce .
#docker run -dit --name py-mcp-server-go-commerce -p 9002:9002 py-mcp-server-go-commerce

FROM python:3.13-slim

RUN apt update && pip install --upgrade pip

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "./app/server.py"] 
