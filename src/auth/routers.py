from fastapi import APIRouter,Depends ,status
from src.auth.schemas import UserCreateModel,UserModel,UserLoginModel,ForgotPasswordConfirmModel,ForgotPasswordRequestModel,EmailModel
from src.auth.service import UserService
from fastapi.exceptions import HTTPException
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.utils import generate_password_hash,create_access_token, decode_token, verify_password
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse 
import random
from src.celery_tasks import send_email
from src.db.redis import add_jti_to_blocklist
from src.mail import mail, create_message
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError
from src.db.models import Users, PasswordResetOtp

from .dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_user,
)

auth_router = APIRouter()
user_service = UserService()

refresh_token_expiry = 2


OTP_EXPIRATION_MINUTES = 10

otp_store = {}

@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    send_email.delay(emails, subject, html)

    return {"message": "Email sent successfully"}



@auth_router.post(
    "/signup",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED
)
async def create_account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),

):
    email = user_data.email 

    user_exist = await user_service.user_exists(email,session)

    if user_exist:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User email already exist")

    new_user = await user_service.create_user(user_data,session)


    access_token = create_access_token(
        user_data={
            'email': new_user.email,
            'user_uid': str(new_user.uid)
        }
    )

    refresh_token = create_access_token(
            user_data={
            'email': new_user.email,
            'user_uid': str(new_user.uid)
        },
        refresh=True,
        expiry=timedelta(days=refresh_token_expiry)
    )

    return JSONResponse(
        content={
            "message":"Login Successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user":{
                "email":new_user.email,
                "uid": str(new_user.uid)
            }
        }
    )
    
    return new_user 


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel,
    session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password

    user_exist = await user_service.get_user_by_email(email,session)

    if user_exist is not None:
        password_valid = verify_password(password,user_exist.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    'email': user_exist.email,
                    'user_uid': str(user_exist.uid)
                }
            )

            refresh_token = create_access_token(
                 user_data={
                    'email': user_exist.email,
                    'user_uid': str(user_exist.uid)
                },
                refresh=True,
                expiry=timedelta(days=refresh_token_expiry)
            )

            return JSONResponse(
                content={
                    "message":"Login Successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user":{
                        "email":user_exist.email,
                        "uid": str(user_exist.uid)
                    }
                }
            )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Email Or Password"
    )



@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: ForgotPasswordRequestModel,session: AsyncSession = Depends(get_session)):
    email = email_data.email
    await user_service.create_password_reset_otp(email,session)
    return {"OTP Has been Sent"}



@auth_router.post("/password-reset-confirm")
async def reset_account_password(
    password_data: ForgotPasswordConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    email = password_data.email
    otp_input = password_data.otp
    new_password = password_data.new_password
    confirm_password = password_data.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # 1️⃣ Query the OTP from DB
        query = select(PasswordResetOtp).where(PasswordResetOtp.email == email)
        result = await session.exec(query)
        stored_otp: PasswordResetOtp = result.first()

        if not stored_otp:
            raise HTTPException(status_code=400, detail="OTP expired or invalid")

        # 2️⃣ Check OTP value
        if stored_otp.otp != otp_input:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # 3️⃣ Check expiration
        if datetime.utcnow() > stored_otp.expires_at:
            await session.delete(stored_otp)
            await session.commit()
            raise HTTPException(status_code=400, detail="OTP expired")

        # 4️⃣ Update user password
        query_user = select(Users).where(Users.email == email)
        user_result = await session.exec(query_user)
        user = user_result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password_hash = generate_password_hash(new_password)

        # 5️⃣ Delete OTP and commit changes
        await session.delete(stored_otp)
        session.add(user)
        await session.commit()

        return JSONResponse(
            content={"message": "Password reset successfully."},
            status_code=status.HTTP_200_OK,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        )





@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )