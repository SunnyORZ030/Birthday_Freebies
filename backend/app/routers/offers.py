from fastapi import APIRouter, HTTPException
from backend.app.data.fake_offers import fake_offers
from backend.app.schemas.offer import OfferResponse

router = APIRouter(
    prefix = "/api/v1/offers",
    tags = ["offers"],
)

@router.get("/", response_model=list[OfferResponse])
def get_ffers():
    return fake_offers

@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer_by_id(offer_id: int):
    for offer in fake_offers:
        if offer["id"] == offer_id:
            return offer
        
    raise HTTPException(status_code=404, detail="offer not found")