from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Test 1 : Sad Path för att testa så att vi får 404 tillbaka
def test_ask_ai_without_data_return_400():
    response = client.post("/ai/ask", json={"question": "Test?"})
    assert response.status_code == 404


# 2.  Happy Path för filuppladdning
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


# 3. NYTT TEST: Sad Path för filuppladdning (fel filtyp)
def test_upload_invalid_file_type_returns_400():
    # ARRANGE: Skapa en ren textfil istället för en CSV
    txt_content = b"Detta ar bara lite vanlig text, ingen riktig data."

    # Notera att vi sätter mime-typen till text/plain och filändelsen till .txt
    files = {"file": ("fel_fil.txt", txt_content, "text/plain")}

    # ACT: Försök ladda upp skräpfilen
    response = client.post("/data/upload", files=files)

    # ASSERT: API:et ska kasta en 400 Bad Request
    assert response.status_code == 400


# 4. kolla health endpointen
def test_health_endpoint_returns_200():
    response = client.get(
        "/health",
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
