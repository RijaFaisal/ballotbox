from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import admin, auth, ballot, products

app = FastAPI(title="BallotBox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(admin.router)
app.include_router(ballot.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
