from pydantic import BaseModel

class OfferResponse(BaseModel):
    id: int
    restaurant_name: str
    title: str
    description: str
    offer_type: str
    is_active: bool