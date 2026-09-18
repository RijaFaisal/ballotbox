from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import admin, admins, auth, candidates, draws, products

app = FastAPI(title="BallotBox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Without this, the browser's CORS same-origin rules hide response
    # headers from JS by default -- the PDF download's filename parsing
    # (client.js) reads this header and silently falls back to a generic
    # name otherwise.
    expose_headers=["Content-Disposition"],
)

app.include_router(auth.router)
app.include_router(admins.router)
app.include_router(products.router)
app.include_router(candidates.router)
app.include_router(draws.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
