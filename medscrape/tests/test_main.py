from fastapi.testclient import TestClient
from medscrape.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_health_check_v1():
    response = client.get("/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "v1"}

def test_run_endpoint():
    test_data = {
        "tld": "https://example.com",
        "questions": ["What is the main topic?", "How many articles?"]
    }
    response = client.post("/run/", json=test_data)
    assert response.status_code == 200
    assert "message" in response.json()
    assert "data" in response.json()
    assert len(response.json()["data"]) == len(test_data["questions"])

def test_process_endpoint():
    test_url = "https://example.com"
    response = client.post("/process/", json={"url": test_url})
    assert response.status_code == 200
    assert response.json()["message"] == "Scraping and processing completed"
    assert response.json()["url"] == test_url
    # Assuming the number of URLs found is variable, check if it's an integer
    assert isinstance(response.json()["urls_found"], int)

def test_query_endpoint():
    test_data = {
        "questions": ["What is the main topic?", "How many articles?"]
    }
    response = client.post("/query/", json=test_data)
    assert response.status_code == 200
    assert "message" in response.json()
    assert "data" in response.json()
    assert len(response.json()["data"]) == len(test_data["questions"])
    for item in response.json()["data"]:
        assert "question" in item
        assert "answer" in item

def test_404_error_handler():
    response = client.get("/nonexistent_endpoint")
    assert response.status_code == 404
    assert response.json() == {"message": "Not Found"}