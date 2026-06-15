from backend.app.data.fake_offers import fake_offers

def get_all_offers():
    return fake_offers

def get_offer_by_id(offer_id: int):
    for offer in fake_offers:
        if offer["id"] == offer_id:
            return offer
        
    return None