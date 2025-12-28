from pydantic import AnyHttpUrl, BaseModel

class Info(BaseModel):
    version: str
    account: str
    app_name: str
    host: str
    port: int
    session_timeout: int
    product_url: AnyHttpUrl
    order_url: AnyHttpUrl