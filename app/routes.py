from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import io

# Skapa en mini app. Hantera det liknande som i node.js
router = APIRouter()

# vi adderar en global variabel för att spara data temorärt i minnet
global_df = None


def get_data_or_400():
    global global_df
    if global_df is None:
        raise HTTPException(
            status_code=400,
            detail="Ingen data har laddats upp. Posta fil till  /data/upload först ",
        )
    return global_df


class ChatRequest(BaseModel):
    query: str


@router.get("/data/stats")
def get_stats(df: pd.DataFrame = Depends(get_data_or_400)):
    return df.describe().to_dict()


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


@router.post("/ai/ask")
def ask_ai(request: ChatRequest, df: pd.DataFrame = Depends(get_data_or_400)):
    stats_text = str(df.describe().to_dict())

    system_prompt = (
        "Du ska uppföra dig som en super expert inom både dataanalys samt även muisiktrender. "
        "Du är kortfarttad, proffessionell samt svara alltid på svenska"
        "Använd följande statiskti för att svara på användarens fråga:\n"
        f"{stats_text}"
        "Avsluta alltid med krama varandra i trafiken"
    )

    user_question = request.query
    full_prompt_to_ai = f"{system_prompt}\n\nAnvändaresn fråga: {user_question}"

    return {
        "status": "framgång",
        "fråga som ställdes": user_question,
        "vad som skickdes till Ain": full_prompt_to_ai,
        "dummy svar": "Här kommer riktigt svar att hanteras snart",
    }
