import uuid
from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class User(SQLModel, table=True):
    email: EmailStr = Field(primary_key=True)
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    credits: int = Field(default=0)
    admin: bool = Field(default=False)
    otp: str | None = Field(default=None)
