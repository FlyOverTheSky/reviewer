from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from contextlib import asynccontextmanager

# Судя по вакансии - вам важна чистота кода, поэтому немного отступил от четкого ТЗ, а именно:

# Добавил для примера простенькие тесты в файл test.py
# Не использовал сырые SQL-запросы - уязвимость к sql-инъекциям
# Вот пример через SQL-запросы

# conn = sqlite3.connect('reviews.db')
# cursor = conn.cursor()
# cursor.execute('''
# INSERT INTO reviews (text, sentiment, created_at)
# VALUES (?, ?, ?)
# ''', (review.text, sentiment, created_at))
# review_id = cursor.lastrowid
# conn.commit()
# conn.close()

# Так же:
# По-хорошему - нужно разбить все на несколько файлов, чтобы не смешивать логику разных модулей
# Что-то в духе: models.py, routes.py, db.py, main.py

DATABASE_URL = "sqlite:///reviews.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Сюда добавляем "хорошие" слова и "плохие" слова
POSITIVE_WORDS = ["хорош", "люблю"]
NEGATIVE_WORDS = ["плохо", "ненавиж"]

#Модель для хранения отзывов
class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

#Модель запроса-добавления отзыва
class ReviewIn(BaseModel):
    text: str

#Модель ответа об отзывах 
class ReviewOut(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    yield

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(lifespan=lifespan)

def analyze_sentiment(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in POSITIVE_WORDS):
        return "positive"
    elif any(word in text_lower for word in NEGATIVE_WORDS):
        return "negative"
    else:
        return "neutral"

@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewIn, db: Session = Depends(get_db)):
    sentiment = analyze_sentiment(review.text)
    db_review = Review(text=review.text, sentiment=sentiment, created_at=datetime.utcnow())

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    result = ReviewOut(
        id=db_review.id,
        text=db_review.text,
        sentiment=db_review.sentiment,
        created_at=db_review.created_at.isoformat()
    )

    return result

@app.get("/reviews", response_model=list[ReviewOut])
def get_reviews(db: Session = Depends(get_db), sentiment=""):
    if sentiment:
        query = db.query(Review).filter(Review.sentiment == sentiment)
    else:
        query = db.query(Review)

    reviews = query.all()
    output_result = [
        ReviewOut(
            id=review.id,
            text=review.text,
            sentiment=review.sentiment,
            created_at=review.created_at.isoformat()
        ) for review in reviews
    ]

    return output_result
