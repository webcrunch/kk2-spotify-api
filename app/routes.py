from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
import io

# Skapa en mini app. Hantera det liknande som i node.js
router = APIRouter()

# vi adderar en global variabel för att spara data temorärt i minnet
global_df = None


class ChatRequest(BaseModel):
    query: str


@router.get("/data/stats")
def get_stats():
    global global_df
    if global_df is None:
        raise HTTPException(status_code=404, detail="Ingen data har laddats upp ännu.")


@router.post("/data/upload")
async def upload_data(file: UploadFile = File(...)):
    global global_df
    # vi verifiera att filen är en csv -> även om det inte kan vara 100 % eftersom man ändå kan manipulera detta.
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Endast CSV filer är tillåtna")
    try:
        conctents = await file.read()
        global_df = pd.read_csv(io.BytesIO(conctents), encoding="utf-8")
        return {
            "message": "Filen har laddats upp",
            "rows": len(global_df),
            "columns": global_df.columns.to_list(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunde inte läsa filen: {str(e)}")
