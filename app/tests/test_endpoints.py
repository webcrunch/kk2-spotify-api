from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Sad Path för att testa så att vi får 400 tillbaka
def test_ask_ai_without_data_return_400():
    response = client.post("/ai/ask", json={"question": "Test?", "context": ""})
    assert response.status_code == 400


# Sad Path för stats
def test_get_stats_without_data_returns_404():
    # ACT: Försök hämta statistik utan att ha laddat upp något dataset
    response = client.get("/data/stats")

    # ASSERT: API:et ska svara med 404 Not Found
    assert response.status_code == 404


def test_upload_too_large_file_returns_400():
    # ARRANGE: Skapa en "fiktiv" fil som är strax över 5MB (t.ex. 6MB)
    # Vi gör detta genom att skapa en sträng med tecken och multiplicera den
    large_content = b"a" * (6 * 1024 * 1024)
    files = {"file": ("stor_fil.csv", large_content, "text/csv")}

    # ACT
    response = client.post("/data/upload", files=files)

    # ASSERT
    assert response.status_code == 400
    assert "stor" in response.json()["detail"].lower()


#  Sad Path för filuppladdning (tom fil)
def test_upload_empty_csv_returns_400():
    # ARRANGE: Skapa en CSV-fil utan något som helst innehåll (0 bytes)
    empty_content = b""
    files = {"file": ("tom_fil.csv", empty_content, "text/csv")}

    # ACT: Försök ladda upp den tomma filen
    response = client.post("/data/upload", files=files)

    # ASSERT: API:et ska kasta en 400 Bad Request
    assert response.status_code == 400


# Happy Path för filuppladdning
def test_upload_valid_csv_returns_200():
    # ARRANGE: Skapa en fejkad CSV-fil i minnet med lite Spotify-data
    csv_content = (
        b"track_name,tempo,danceability\nSuperlat,120.5,0.8\nSnabblat,180.0,0.4"
    )

    # Packa in den i det format som TestClient förväntar sig (fältnamn, filnamn, innehåll, mime-typ)
    files = {"file": ("test_data.csv", csv_content, "text/csv")}

    # ACT: Skicka filen till din upload-endpoint
    response = client.post("/data/upload", files=files)

    # ASSERT: Verifiera att API:et tog emot filen och svarar med 200 OK
    assert response.status_code == 200

    # Valfritt: Kolla att svarsmeddelandet bekräftar uppladdningen
    json_data = response.json()
    assert (
        json_data["rows"] == 2
    )  # Vi skickade ju in 2 datarader (Superlat och Snabblat)
    assert "tempo" in json_data["columns"]  # Kolla så att tempo-kolumnen hittades


# Sad Path för filuppladdning (fel filtyp)
def test_upload_invalid_file_type_returns_400():
    # ARRANGE: Skapa en ren textfil istället för en CSV
    txt_content = b"Detta ar bara lite vanlig text, ingen riktig data."

    # Notera att vi sätter mime-typen till text/plain och filändelsen till .txt
    files = {"file": ("fel_fil.txt", txt_content, "text/plain")}

    # ACT: Försök ladda upp skräpfilen
    response = client.post("/data/upload", files=files)

    # ASSERT: API:et ska kasta en 400 Bad Request
    assert response.status_code == 400


# Verifiera health endpointen
def test_health_endpoint_returns_200():
    response = client.get(
        "/health",
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
