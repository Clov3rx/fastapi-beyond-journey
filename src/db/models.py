from sqlmodel import SQLModel,Field,Column,func,Integer,LargeBinary,ForeignKey
import sqlalchemy.dialects.postgresql as pg 
import uuid 
from datetime import datetime


class Users(SQLModel,table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            index=True,
            nullable=False,
            default=uuid.uuid4
        )
    )
    username: str
    email: str
    password_hash: str = Field(exclude=True)
    is_verified: bool = Field(default=False)



    def __repr__(self):
        return f"<Users {self.username}>"




class PasswordResetOtp(SQLModel, table=True):
    __tablename__ = "otp"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    otp: str
    expires_at: datetime


    def __repr__(self):
        return f"<Users {self.email}>"


class Images(SQLModel, table=True):
    __tablename__ = "images"

    id: int = Field(
        sa_column=Column(
            Integer,
            primary_key=True,
            index=True
        )
    )

    filename: str

    data: bytes = Field(
        sa_column=Column(LargeBinary, nullable=False)
    )

    owner_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            ForeignKey("users.uid"),
            nullable=False,
            index=True
        )
    )

    def __repr__(self):
        return f"<Image {self.filename}>"
