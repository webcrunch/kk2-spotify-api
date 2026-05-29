from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# skapa en limiter. Ip addesserna används för att hålla koll på antalet anrop.
limiter = Limiter(key_func=get_remote_address)
# problem med cirkulärt beroende om jag har denna ovanför Limiter instansen
from app.routes import router

app = FastAPI(title="Spotify Orakel API", description="KK2 kedja med AI för dataanalys")

# Addera slowApis felhanterare med FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Här kopplar vi in de routes som vi skapade i den andra filen
app.include_router(router)


# vi behåller health check för default
@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
