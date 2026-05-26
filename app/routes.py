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
