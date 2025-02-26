from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class User(SQLModel, table=True):
    email: EmailStr = Field(primary_key=True)
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    credits: int = Field(default=0)
    admin: bool = Field(default=False)
    otp: str | None = Field(default=None)


class Note(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user: str = Field(foreign_key="user.email")
    updated: datetime = Field(default_factory=datetime.now)
    content: str
