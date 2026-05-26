from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import io
import logging
import os
from app.llm import spotify_pipeline, PipelineInput, StructuredResponse

router = APIRouter()
global_df = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str


def get_data_or_404():
    global global_df
    if global_df is None:
        logger.error(f"Ingen data har laddats upp. Kör /data/upload först!")
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
        logger.error("Kunde inte läsa filen: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Kunde inte läsa filen: {str(e)}")


@router.get("/data/stats")
def get_stats(df: pd.DataFrame = Depends(get_data_or_404)):
    return df.describe().to_dict()


@router.post("/ai/ask", response_model=StructuredResponse)
def ask_ai(request: ChatRequest, df: pd.DataFrame = Depends(get_data_or_404)):
    try:
        # 1. Definiera vilka kolumner vi helst vill analysera
        target_columns = ["danceability", "tempo", "energy", "loudness"]

        # 2. Dynamisk kontroll: Ta bara de kolumner som faktiskt existerar i filen
        available_columns = [col for col in target_columns if col in df.columns]

        # Fallback: Om ingen av målkolumnerna hittades, ta filens 4 första kolumner
        if not available_columns:
            logger.warning(
                "Inga målkolumner matchade. Använder fallback på filens första kolumner."
            )
            available_columns = df.columns[:4].tolist()

        # 3. Plocka ut beskrivande statistik för de tillgängliga kolumnerna
        stats_dict = df[available_columns].describe().loc[["mean", "max"]].to_dict()

        # 4. Skapa input-modellen (Synkad med question-fältet)
        incoming_data = PipelineInput(
            question=request.question, stats_text=str(stats_dict)
        )

        # 5. Kör igång din helt egna Runnable-kedja!
        return spotify_pipeline.invoke(incoming_data)

    except Exception as e:
        logger.error(f"Pipeline kraschade: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline kraschade: {str(e)}")


# @router.post("/ai/ask", response_model=StructuredResponse)
# def ask_ai(request: ChatRequest, df: pd.DataFrame = Depends(get_data_or_404)):
#     try:
#         # Vi plockar ut de mest relevanta kolumnerna och värdena
#         # för att hålla prompten kort och fokuserad för vår lokala modell
#         stats_dict = (
#             df[["danceability", "tempo", "energy", "loudness"]]
#             .describe()
#             .loc[["mean", "max"]]
#             .to_dict()
#         )

#         incoming_data = PipelineInput(
#             query=request.question, stats_text=str(stats_dict)
#         )

#         # Kör igång din helt egna Runnable-kedja!
#         return spotify_pipeline.invoke(incoming_data)

#     except Exception as e:
#         logger.error(f"Pipeline kraschade: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Pipeline kraschade: {str(e)}")
