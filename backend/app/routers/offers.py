from fastapi import APIRouter, HTTPException
from backend.app.data.fake_offers import fake_offers

router = APIRouter(
    prefix = "/api/v1/offers",
    tags = ["offers"],
)

@router.get("/")
def get_ffers():
    return fake_offers

@router.get("/{offer_id}")
def get_offer_by_id(offer_id: int):
    for offer in fake_offers:
        if offer["id"] == offer_id:
            return offer
        
    raise HTTPException(status_code=404, detail="offer not found")