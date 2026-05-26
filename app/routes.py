from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import io


from transformers import pipeline

router = APIRouter()
global_df = None

print("Startar den lokala ai motorn")
local_llm = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-135M-Instruct")
print("Ai Motorn fördig")


class ChatRequest(BaseModel):
    query: str


def get_data_or_400():
    global global_df
    if global_df is None:
        raise HTTPException(
            status_code=400,
            detail="Ingen data har laddats upp. Posta fil till /data/upload först ",
        )
    return global_df


@router.get("/data/stats")
def get_status(df: pd.DataFrame = Depends(get_data_or_400)):
    return df.describe().to_dict()


@router.post("/data/upload")
async def upload_data(file: UploadFile = File(...)):

    # vi verifiera att filen är en csv -> även om det inte kan vara 100 % eftersom man ändå kan manipulera detta.
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Endast CSV-filer är tillåtna.")
    try:
        contents = await file.read()
        global_df = pd.read_csv(io.BytesIO(contents), encoding="utf-8")
        return {"message": "Filen har laddats upp!", "rows": len(global_df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunde inte läsa filen: {str(e)}")


@router.post("/ai/ask")
def ask_ai(request: ChatRequest, df: pd.DataFrame = Depends(get_data_or_400)):
    # stats_text = str(df.describe().to_dict())
    stats_dict = df.describe().loc[["mean", "min", "max"]].to_dict()
    stats_text = str(stats_dict)

    system_prompt = (
        "Du är en expert på dataanalys och musiktrender. "
        "Du är kortfattad, professionell och svarar alltid på svenska. "
        f"Använd följande statistik för att svara på användarens fråga:\n{stats_text}\n"
        "Avsluta alltid med 'krama varandra i trafiken'."
    )

    user_question = request.query

    # bygger om texten till en enda stor textsträng för att lokala transformers ska hantera den
    full_prompt = f"{system_prompt}\n\nFråga: {user_question}\nSvar:"

    try:
        # här kör vi modellen på den lokala maskinen
        response = local_llm(full_prompt, max_new_token=150, truncate=True)

        # Vi städar upp texten så att vi bara hanterar svaret från Ain
        raw_output = response[0]["generated-text"]
        ai_svar = raw_output.split("Svar;")[-1].strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lokala AI:n kraschade: {str(e)}")

    return {
        "status": "framgång",
        "fråga som ställdes": user_question,
        "ai_svar": ai_svar,
    }
