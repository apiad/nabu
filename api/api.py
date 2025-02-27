import json
import math
import httpx
import random
import openai
from uuid import uuid4
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import EmailStr
from models import Config, Note, Pack, Process, Style, User
import prompts
from sqlmodel import SQLModel, Session, create_engine, select
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

ADMIN = os.getenv("ADMIN")

TRANSCRIPTION_API_HOST = os.getenv("TRANSCRIPTION_API_HOST")
TRANSCRIPTION_API_MODEL = os.getenv("TRANSCRIPTION_API_MODEL")
TRANSCRIPTION_API_KEY = os.getenv("TRANSCRIPTION_API_KEY")

LLM_API_HOST = os.getenv("LLM_API_HOST")
LLM_API_MODEL = os.getenv("LLM_API_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

SKIP_EMAIL = bool(os.getenv("SKIP_EMAIL"))

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


create_db_and_tables()

app = FastAPI()


@app.post("/login")
async def login(email: EmailStr):
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])

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
    if SKIP_EMAIL:
        print(receiver_email, otp)
        return

    """Send OTP via email using Migadu SMTP asynchronously."""
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = "OTP Verification"

    body = f"Your OTP for Nabu Voice Notes is:\n\n{otp}"
    msg.attach(MIMEText(body, "plain"))

    smtp_server = EMAIL_HOST
    port = int(EMAIL_PORT)

    async with SMTP(hostname=smtp_server, port=port, use_tls=True) as server:
        await server.login(SENDER_EMAIL, SENDER_PASSWORD)
        await server.send_message(msg)


@app.post("/verify")
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


@app.get("/config")
async def get_config(email: EmailStr, token: str) -> Config:
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.token != token:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user.get_config(session)


@app.post("/config")
async def set_config(email: EmailStr, token: str, config: Config):
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.token != token:
            raise HTTPException(status_code=401, detail="Invalid token")

        user.set_config(session, config)
        return {"message": "Config updated."}


async def process_note(
    transcription: str, mode: str, style: Style, processes: list[Process]
):
    client = openai.AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_API_HOST)

    if mode == "transcription":
        prompt = prompts.TRANSCRIPTION_PROMPT
    else:
        prompt = prompts.INSTRUCTION_PROMPT

    messages = [
        dict(role="system", content=prompt.format(style=style.description)),
        dict(role="user", content=transcription),
    ]

    response = await client.chat.completions.create(
        model=LLM_API_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    usage = response.usage.total_tokens

    for process in processes:
        messages = [
            dict(role="system", content=prompts.PROCESS_PROMPT.format(process=process.prompt)),
            dict(role="user", content=transcription),
        ]

        response = await client.chat.completions.create(
            model=LLM_API_MODEL,
            messages=messages
        )

        d = response.choices[0].message.content
        data['content'] += f"\n\n**{process.name}**\n\n{d}"
        usage += response.usage.total_tokens

    data["cost"] = math.ceil(usage / 1000)

    return data


@app.post("/process")
async def process(email: EmailStr, token: str, file: UploadFile, mode: str, style:str, processes:str) -> Note:
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if file.content_type != "audio/wav":
            raise HTTPException(status_code=400, detail="Invalid file type")

        if user.credits <= 0:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        if mode not in ["transcription", "instruction"]:
            raise HTTPException(status_code=400, detail="Invalid mode")

        config = user.get_config(session)

        possible_styles = [s for s in config.styles if s.name == style]

        if not possible_styles:
            raise HTTPException(status_code=400, detail="Invalid style")

        processes = set(processes.split(","))

        user_style = possible_styles[0]
        user_processes = [p for p in config.processes if p.name in processes]

        audio = await file.read()

        print("Received audio file: ", len(audio))

        client = openai.AsyncOpenAI(
            api_key=TRANSCRIPTION_API_KEY, base_url=TRANSCRIPTION_API_HOST
        )

        transcription = await client.audio.transcriptions.create(
            model=TRANSCRIPTION_API_MODEL,
            file=audio,
            response_format="text",
        )

        print("Transcription ready: ", len(transcription))

        data = await process_note(transcription, mode, user_style, user_processes)

        print("Processing ready: ", len(data["content"]))

        note = Note(user=email, content=data["content"], title=data["title"])
        session.add(note)

        user.credits -= data["cost"]
        session.add(user)

        session.commit()
        session.refresh(note)

        return note


@app.get("/notes")
async def get_notes(email: EmailStr, token: str) -> list[Note]:
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        notes = session.exec(select(Note).where(Note.user == email)).all()

    return notes


@app.delete("/note/{id}")
async def delete_note(email: EmailStr, token: str, id: str):
    with Session(engine) as session:
        user: User = session.get(User, email)
        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        note: Note = session.get(Note, id)

        if note is None or note.user != email:
            raise HTTPException(status_code=404, detail="Note not found")

        session.delete(note)
        session.commit()

    return {"detail": "Note deleted"}


@app.get("/credits")
def get_credits(email: EmailStr, token: str):
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return {"remaining": user.credits}


CREDIT_PRODUCTS = {
    "100 Credits": "RBGp66ccm3dTedX9mv9T9A==",
    "250 Credits": "lPqbI6kRPJtqrGRYPqpYIA==",
    "500 Credits": "gtonvp-BcpF-TZ1VFYCT2g==",
    "1000 Credits": "Wb9M4K5An8aGb9yJ1aMThA==",
    "10000 Credits": "xbIVi2Qv5oNap6wp9oWdgg==",
}

CREDIT_VALUES = {
    "100 Credits": 100,
    "250 Credits": 250,
    "500 Credits": 500,
    "1000 Credits": 1000,
    "10000 Credits": 10000,
}


@app.post("/credits")
def add_credits(email: EmailStr, token: str, pack: str, key: str):
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if session.get(Pack, key):
            raise HTTPException(status_code=400, detail="Key already used")

        url = "https://api.gumroad.com/v2/licenses/verify"
        params = dict(
            product_id=CREDIT_PRODUCTS[pack],
            license_key=key,
            increment_uses_count=False,
        )

        client = httpx.Client()
        response = client.post(url, params=params)

        if response.json()["success"]:
            session.add(Pack(id=key, amount=CREDIT_VALUES[pack], user=email))

            user.credits += CREDIT_VALUES[pack]
            session.add(user)

            session.commit()
            session.refresh(user)

            return {"remaining": user.credits, "status": "accepted"}

        else:
            raise HTTPException(status_code=400, detail="Invalid key")


@app.get("/users")
async def get_users(email: EmailStr, token: str):
    with Session(engine) as session:
        user: User = session.get(User, email)

        if user is None or user.token != token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if user.email != ADMIN:
            raise HTTPException(status_code=401, detail="Need to be admin")

        users = session.exec(select(User)).all()
        return users
