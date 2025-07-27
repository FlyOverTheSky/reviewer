from sqlalchemy import text
from fastapi.testclient import TestClient
from main import app, get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

response = client.post("/reviews", json={"text": "Я люблю этот продукт"})
assert response.status_code == 200
data = response.json()
assert data["sentiment"] == "positive"
assert "id" in data
assert "created_at" in data

with TestingSessionLocal() as db:
    db.execute(text("DELETE FROM reviews"))
    db.commit()

client.post("/reviews", json={"text": "Я люблю этот продукт"})
client.post("/reviews", json={"text": "Этот продукт плохо"})
client.post("/reviews", json={"text": "Продукт нормальный"})

response = client.get("/reviews?sentiment=negative")
assert response.status_code == 200
data = response.json()
assert len(data) == 1
assert data[0]["sentiment"] == "negative"
print("тестирование завершено")

with TestingSessionLocal() as db:
    db.execute(text("DELETE FROM reviews"))
    db.commit()