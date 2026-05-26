from fastapi import FastAPI

# här importerar vi vår router fil
from app.routes import router

app = FastAPI(title="Spotify Orakel API", description="KK2 kedja med AI för dataanalys")

# Här kopplar vi in de routes som vi skapade i den andra filen
app.include_router(router)


# vi behåller health check för default
@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
