from fastapi import FastAPI
from models import User
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
