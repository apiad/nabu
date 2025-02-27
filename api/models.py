from datetime import datetime
import uuid
import json
from sqlmodel import SQLModel, Field, Session
from pydantic import EmailStr


class Style(SQLModel):
    name: str
    description: str


class Process(SQLModel):
    name: str
    prompt: str


class Config(SQLModel):
    styles: list[Style]
    processes: list[Process]

    @classmethod
    def default(cls):
        return cls(
            styles=[
                Style(name="Plain", description="Plan text written in the same style and as close as possible to the original."),
                Style(name="Formal", description="Formal text written with technically accurate and domain-specific terms."),
                Style(name="Verbose", description="Verbose text written with extra details relevant to the original text that aren't mentioned explicitly."),
                Style(name="Bullets", description="Text written in bullet points with concise and clear points that summarize the original text."),
                Style(name="Concise", description="Concise text written with the most important information from the original text."),
            ],
            processes=[
                Process(name="Summary", prompt="Summarize the text in a concise language."),
                Process(name="Explanation", prompt="Explain the text in a detailed and clear language."),
                Process(name="Actions", prompt="Extract all actionable items mentioned in the text, as a list of bullets."),
                Process(name="Follow up", prompt="Suggest follow up actions or questions based on the text, as a list of bullets.")
            ]
        )


class User(SQLModel, table=True):
    email: EmailStr = Field(primary_key=True)
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    credits: int = Field(default=10)
    admin: bool = Field(default=False)
    otp: str | None = Field(default=None)

    def set_config(self, session: Session, config: Config):
        data = json.dumps(config.model_dump(mode='json'))

        config_obj = session.get(UserConfig, self.email)

        if config_obj:
            config_obj.data = data
        else:
            config_obj = UserConfig(user=self.email, data=data)

        session.add(config_obj)
        session.commit()

    def get_config(self, session: Session) -> Config:
        config_obj = session.get(UserConfig, self.email)

        if config_obj:
            return Config(**json.loads(config_obj.data))
        else:
            return Config.default()


class Note(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user: str = Field(foreign_key="user.email")
    updated: datetime = Field(default_factory=datetime.now)
    content: str
    title: str


class Pack(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user: str = Field(foreign_key="user.email")
    created: datetime = Field(default_factory=datetime.now)
    amount: int


class UserConfig(SQLModel, table=True):
    user: str = Field(foreign_key="user.email", primary_key=True)
    data: str
