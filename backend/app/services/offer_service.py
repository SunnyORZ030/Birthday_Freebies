from backend.app.repositories.offer_repository import (
    fetch_all_offers,
    fetch_offer_by_id,
)

def get_all_offers():
    return fetch_all_offers()

def get_offer_by_id(offer_id: int):
    return fetch_offer_by_id(offer_id)