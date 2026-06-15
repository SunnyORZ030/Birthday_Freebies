from fastapi import APIRouter, HTTPException
from backend.app.schemas.offer import OfferResponse
from backend.app.services.offer_service import get_all_offers, get_offer_by_id

router = APIRouter(
    prefix = "/api/v1/offers",
    tags = ["offers"],
)

@router.get("/", response_model=list[OfferResponse])
def get_ffers():
    return get_all_offers()

@router.get("/{offer_id}", response_model=OfferResponse)
def read_offer_by_id(offer_id: int):
    offer = get_offer_by_id(offer_id)
    
    if offer is None:
        raise HTTPException(status_code=404, detail="offer not found")
    
    return offer