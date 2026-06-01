# KK2 – Oraklet: AI Data Analyzer API

*Ett starkt typat REST-API byggt med FastAPI som kombinerar traditionell dataanalys i Pandas med lokal AI-inferens. Tjänsten låter användare ladda upp dataset och ställa naturliga frågor om datan. Svaren genereras genom en egendesignad, orkestrerad Runnable-kedja.*

**Utvecklad som slutinlämning i Kunskapskontroll 2.**

---

## ✨ Utmärkande funktioner

* **Egen Runnable-kedja:** Kärnan i applikationen är en typad pipeline (`PromptBuilder` | `LLMRunner` | `ResponseParser`) där varje steg valideras med Pydantic-modeller.
* **Dynamisk Datatolkning:** API:et är robust och hanterar inte bara de kravställda `.csv`-filerna, utan packar även upp `.xlsx` och `.xls` dynamiskt i bakgrunden med hjälp av `openpyxl`. Den har även fallback-logik för att alltid hitta relevant data att analysera.
* **Lokal AI via Transformers & Ollama:** Integrerad med `HuggingFaceTB/SmolLM2-135M-Instruct` via pipeline, men byggd med ett abstraktionslager som gör det möjligt att blixtsnabbt växla över till större modeller (ex. Llama 3.2 via Ollama) genom miljövariabler.
* **Separation of Concerns:** Routers, Pydantic-scheman, kedjelogik och tester är strikt separerade i en tydlig projektstruktur.

---

## 🛠️ Arkitektur & Kedjedesign

När ett POST-anrop görs till `/ai/ask` slussas datan genom följande typade Pydantic-kedja:

- 1.  `PromptBuilder[PipelineInput, PromptPayload]`: Formaterar systeminstruktionerna, bygger in den statistiska kontexten (från Pandas) och applicerar ChatML-taggar.
- 2.  `LLMRunner[PromptPayload, RawLLMOutput]`: Hanterar inferensen. Känner av `.env`-konfigurationen och kör antingen modellen lokalt i minnet via HuggingFace eller skickar en payload till en instansierad Ollama-container.
- 3.  `ResponseParser[RawLLMOutput, StructuredResponse]`: Tolkar modellens råoutput, städar bort ChatML-taggar och extraherar det relevanta svaret till ett strukturerat JSON-format för klienten.

---


## 🚀 Installation & Körning

### Krav (Requirements)
* Python 3.10+
* Docker & Docker Compose(Valfritt)
* [uv](https://github.com/astral-sh/uv) (Pakethanterare)

### 1. Klona och installera beroenden

```bash
# Klona repot
git clone git@github.com:webcrunch/kk2-spotify-api.git
cd kk2-oraklet

# Synka och installera alla beroenden via uv
uv sync
```

### 2. Miljövariabler

Kopiera .env.example till en ny fil döpt till .env (denna ignoreras av Git av säkerhetsskäl).


``` bash 
# Välj leverantör: 'huggingface' (Standard) eller 'ollama'
AI_PROVIDER=huggingface

# Om du använder Ollama (Frivilligt)
MODEL_NAME=llama3.2
OLLAMA_URL=http://localhost:11434
``` 
### 3. Starta AI-motorn (Docker & Ollama) Valfritt
För att API:et ska kunna kommunicera med den större AI-modellen behöver vi starta Docker-miljön.

I docker compose filen bestämmer du vilken modell som du vill köra med. 
``` bash 
 command:
      - "-c"
      - |
        echo "Väntar på att Ollama-servern ska starta..."
        until ollama list > /dev/null 2>&1; do sleep 2; done

        echo "Laddar ner Llama 3.2..."
        ollama pull llama3.2

        echo "Modellen är redo att användas!"

```

Här ser vi i exemplet att den kommer att ladda ned modellen llama 3.2


``` bash 
# Starta containern i bakgrunden via docker-compose
docker compose up -d
```
### 4. Starta servern

``` bash 
uv run uvicorn app.main:app --reload
```

API:et och den interaktiva Swagger-dokumentationen finns nu tillgänglig på: http://127.0.0.1:8000/docs

## 📡 Endpoints

- **GET** /health
Returnerar API:ets hälsostatus {"status": "ok"}.

- **GET** /data/stats
Returnerar beskrivande statistik (från df.describe()). Om ingen fil är uppladdad returneras statuskod 404.

- **POST** /data/upload
Accepterar uppladdning av dataset (stöder filformaten .csv).
 Läser in filen till en Pandas DataFrame i minnet och returnerar metadata (rader, kolumner, datatyper).

- ***POST** /ai/ask
Fråga oraklet! Tar emot en JSON-payload (t.ex. {"question": "Vilken stad har högst medeltemperatur?"}) och returnerar ett AI-genererat svar baserat på den uppladdade datan.

## 🧪 Tester (Pytest)

Applikationen täcks av en automatiserad testsvit som säkerställer att både API-routes och de individuella kedjestegen fungerar som förväntat. Testsviten använder monkeypatch för att garantera isolerade och deterministiska tester, oberoende av lokala miljövariabler.

#### Kör testerna med:

```bash 
uv run pytest app/tests/ -v
```

ha så kul :) 