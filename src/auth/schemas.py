from pydantic import BaseModel,Field, EmailStr
import uuid 
from typing import List
from datetime import datetime




class UserCreateModel(BaseModel):
    username: str = Field(max_length=8)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    password_hash: str = Field(exclude=True)
    is_verified: bool 

class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)



class EmailModel(BaseModel):
    addresses : List[str]

class OtpCreateModel(BaseModel):
    email: str
    otp: str
    expires_at: datetime


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str


class ForgotPasswordRequestModel(BaseModel):
    email: str


class ForgotPasswordConfirmModel(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_new_password: str


