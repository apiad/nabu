import random
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import EmailStr
from models import User
from sqlmodel import SQLModel, Session, create_engine
from aiosmtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import dotenv
import os

dotenv.load_dotenv()

# load all environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()

app = FastAPI()


@app.get("/login")
async def login(email: EmailStr):
    otp = "".join([str(random.randint(0,9)) for _ in range(6)])

    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None:
            user = User(email=email, otp=otp)

        user.otp = otp
        session.add(user)
        session.commit()

    await send_email(email, otp)

    return {"message": "OTP sent successfully"}


async def send_email(receiver_email, otp):
    """Send OTP via email using Migadu SMTP asynchronously."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = "OTP Verification"

    body = f"Your OTP for Nabu Voice Notes is:\n\n{otp}"
    msg.attach(MIMEText(body, 'plain'))

    smtp_server = EMAIL_HOST
    port = int(EMAIL_PORT)

    async with SMTP(hostname=smtp_server, port=port, use_tls=True) as server:
        await server.login(SENDER_EMAIL, SENDER_PASSWORD)
        await server.send_message(msg)


@app.get("/verify")
async def verify_otp(email: EmailStr, otp: str):
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.otp is None:
            raise HTTPException(status_code=400, detail="OTP not sent")

        if user.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        user.token = uuid4().hex
        user.otp = None

        session.add(user)
        session.commit()

        return {"message": "User verified.", "token": user.token}
