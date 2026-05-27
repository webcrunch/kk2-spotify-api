En markdown/pdf (1–2 A4-sidor) som täcker följande punkter. Använd gärna konkreta exempel från din egen kod.

1. Säkerhetsaspekter
Hur skyddar du API-nycklar? Vad hade hänt om .env checkats in i Git?
Vilka risker finns med att ta emot godtyckliga filuppladdningar? Hur har du hanterat dem?
Prompt injection: kan en användare få modellen att göra något den inte ska genom att formulera frågan på ett visst sätt? Ge ett konkret exempel på en injection och hur du skulle kunna mitigra den.
2. Dataskydd (GDPR)
Anta att dataseten som laddas upp kan innehålla personuppgifter. Vilka problem innebär det för din tjänst så som den är utformad nu?
Vad skulle krävas om tjänsten skulle sättas i produktion?
3. AI-risker och ansvar
Vilka begränsningar har en liten modell som SmolLLM jämfört med större modeller? Hur påverkar det kvaliteten på svaren?
Ge ett konkret exempel på bias (partiskhet) som skulle kunna uppstå.
Hur skulle du testa att din kedja är tillförlitlig? (Tips: pytest – du kan mocka modellen.)
4. Designval
Varför är Runnable-mönstret med |-operatorn kraftfullt? Jämför med att skriva all logik i en enda funktion.
Vad var det största tekniska hindret och hur löste du det?
