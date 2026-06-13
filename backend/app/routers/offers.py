from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix = "/api/v1/offers",
    tags = ["offers"],
)

fake_offers = [
    {
        "id" : 1,
        "restaurant_name" : "Starbucks",
        "title" : "Free Birthday drink",
        "descreption" : "Get your free drinks on your birthday.",
        "offer_type" : "drink",
        "is_active" : True,
    },
    {
        "id" : 2,
        "restaurant_name" : "Denny's",
        "title" : "Get a free Grand Slam breakfast on your birthday.",
        "offer_type" : "meal",
        "is_active" : True,
    },
]

@router.get("/")
def get_ffers():
    return fake_offers

@router.get("/{offer_id}")
def get_offer_by_id(offer_id: int):
    for offer in fake_offers:
        if offer["id"] == offer_id:
            return offer
        
    raise HTTPException(status_code=404, detail="offer not found")