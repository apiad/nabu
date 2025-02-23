import uuid
from sqlmodel import SQLModel, Field, UUID


class User(SQLModel, table=True):
    username: str = Field(primary_key=True)
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    credits: int = Field(default=0)
    admin: bool = Field(default=False)
    topt: str = Field(default="123456")
