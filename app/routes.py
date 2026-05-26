from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import io

from app.llm import spotify_pipeline, PipelineInput, StructuredResponse

router = APIRouter()
global_df = None


class ChatRequest(BaseModel):
    query: str


def get_data_or_404():
    global global_df
    if global_df is None:
        raise HTTPException(
            status_code=404,
            detail="Ingen data har laddats upp. Kör /data/upload först!",
        )
    return global_df


@router.post("/data/upload")
async def upload_data(file: UploadFile = File(...)):
    global global_df
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Endast CSV-filer är tillåtna.")
    try:
        contents = await file.read()
        global_df = pd.read_csv(io.BytesIO(contents), encoding="utf-8")
        return {
            "rows": len(global_df),
            "columns": global_df.columns.tolist(),
            "dtypes": global_df.dtypes.astype(str).to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunde inte läsa filen: {str(e)}")


@router.get("/data/stats")
def get_stats(df: pd.DataFrame = Depends(get_data_or_404)):
    return df.describe().to_dict()


@router.post("/ai/ask", response_model=StructuredResponse)
def ask_ai(request: ChatRequest, df: pd.DataFrame = Depends(get_data_or_404)):
    try:
        # Vi plockar ut de mest relevanta kolumnerna och värdena
        # för att hålla prompten kort och fokuserad för vår lokala modell
        stats_dict = (
            df[["danceability", "tempo", "energy", "loudness"]]
            .describe()
            .loc[["mean", "max"]]
            .to_dict()
        )

        incoming_data = PipelineInput(query=request.query, stats_text=str(stats_dict))

        # Kör igång din helt egna Runnable-kedja!
        return spotify_pipeline.invoke(incoming_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline kraschade: {str(e)}")
