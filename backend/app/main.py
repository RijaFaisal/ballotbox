from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, draws, entries

app = FastAPI(title="BallotBox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries.router)
app.include_router(auth.router)
app.include_router(draws.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
