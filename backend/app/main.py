from fastapi import FastAPI
from backend.app.routers import offers

app = FastAPI(
    title = "Birthday Freebies API",
    description = "Backend API for the Birthday Freebies Tracker project.",
    version = "0.1.0"
)

app.include_router(offers.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Birthdat Freebies API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}