from pydantic import BaseModel

class Receipt(BaseModel):
    date: str
    service: str
    detail: str
    price: int
