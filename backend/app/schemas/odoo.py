from pydantic import BaseModel


class OdooConfigIn(BaseModel):
    url: str = ""
    db: str = ""
    username: str = ""
    api_key: str = ""
    company_id: int = 1
    protocol: str = "jsonrpc"


class OdooConfigOut(BaseModel):
    url: str
    db: str
    username: str
    company_id: int
    protocol: str
    configured: bool
    # api_key wird nie ausgegeben (nur ob gesetzt)
    api_key_set: bool
