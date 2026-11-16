from fastapi.testclient import TestClient
from app.main import app
from app.config import MODULES

def test_pages():
    with TestClient(app) as c:
        for slug,label in MODULES:assert c.get("/"+slug).status_code==200
def test_api_and_export():
    with TestClient(app) as c:
        a=c.post("/api/runs",json={"sample":"dirty"}).json();rid=a["manifest"]["run_id"]
        assert c.get(f"/api/runs/{rid}/evidence.csv").status_code==200
        assert a["reconciliation"]["time_ok"] is True
def test_wrong_csv():
    with TestClient(app) as c:assert c.post("/api/runs",json={"text":"a,b\n1,2"}).status_code==422

def test_percentages_in_page():
    with TestClient(app) as c:
        page=c.get("/calculate").text
        assert "83.33%" in page and "63.33%" in page
        assert "0.833333333333" not in page.split("title=",1)[0]
