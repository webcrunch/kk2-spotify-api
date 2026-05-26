from fastapi import FastAPI

app = FastAPI(title="Spotify Orakel API", description="KK2 AI-kedja för dataanalys")


@app.get("/health")
def health_check():
    return {"status": "ok"}
