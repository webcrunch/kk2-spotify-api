from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import io
import logging
import os
from app.llm import spotify_pipeline, PipelineInput, StructuredResponse
import hashlib
from cachetools import TTLCache
from fastapi import Request
from app.main import limiter

# ----- INSTANSIERA JOHNNY CACHE ------

# max_size : 100 . Det sparas max hundra unika svar åt gången
# ttl = 3600 . Svaren raderas automatiskt efter en timme.

johnny_cache = TTLCache(maxsize=100, ttl=3600)


# skapa en hjälpfunktion för att skapa unikna hash utifrån fråga och datan
def generate_cache_key(question: str, dataset_stats: str) -> str:
    # frågan och statisktien slås ihopa till en sträng och hashas.
    # om frågan eller datan ändras kommer det att bli en ny nyckel.
    raw_string = f"{question}|{dataset_stats}".encode("utf-8")
    return hashlib.sha256(raw_string).hexdigest()


router = APIRouter()
global_df = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    context: str


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
@limiter.limit("5/minute")
async def upload_data(request: Request, file: UploadFile = File(...)):
    global global_df

    # 1. Kontrollera att filen endast är en CSV-fil
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Endast CSV-filer är tillåtna.",
        )

    try:
        contents = await file.read()

        # Läs in filen direkt med Pandas
        global_df = pd.read_csv(io.BytesIO(contents), encoding="utf-8")

        return {
            "rows": len(global_df),
            "columns": global_df.columns.tolist(),
            "dtypes": global_df.dtypes.astype(str).to_dict(),
        }
    except Exception as e:
        logger.error(f"Kunde inte läsa filen: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Kunde inte läsa filen: {str(e)}")


@router.get("/data/stats")
def get_stats(df: pd.DataFrame = Depends(get_data_or_404)):
    return df.describe().to_dict()


@router.post("/ai/ask", response_model=StructuredResponse)
@limiter.limit("5/minute")
def ask_ai(
    request: Request,
    chat_payload: ChatRequest,
    df: pd.DataFrame = Depends(get_data_or_404),
):
    try:
        #  Definiera vilka kolumner vi helst vill analysera
        target_columns = ["danceability", "tempo", "energy", "loudness"]

        #  Dynamisk kontroll: Ta bara de kolumner som faktiskt existerar i filen
        available_columns = [col for col in target_columns if col in df.columns]

        # Fallback: Om ingen av målkolumnerna hittades, ta filens 4 första kolumner
        if not available_columns:
            logger.warning(
                "Inga målkolumner matchade. Använder fallback på filens första kolumner."
            )
            available_columns = df.columns[:4].tolist()

        # 3. Plocka ut beskrivande statistik för de tillgängliga kolumnerna
        stats_dict = df[available_columns].describe().loc[["mean", "max"]].to_dict()
        stats_text = str(stats_dict)
        # 4. Kontrollera cachen
        cache_key = generate_cache_key(chat_payload.question, stats_dict)

        if cache_key in johnny_cache:
            logger.info("⚡ Cache hit!. Johnny leverar svaret från minnet. ⚡")
            return johnny_cache[cache_key]

        logger.info("🐢 Cache miss. Skickar frågan till AI-modellen...")
        # 5. Skapa input-modellen (Synkad med question-fältet)
        incoming_data = PipelineInput(
            question=chat_payload.question,
            stats_text=str(stats_dict),
            context=chat_payload.context,
        )

        # 6. Kör igång din helt egna Runnable-kedja!
        result = spotify_pipeline.invoke(incoming_data)

        # 7. Spara svaret i cachen till nästa gång
        johnny_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"Pipeline kraschade: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline kraschade: {str(e)}")
