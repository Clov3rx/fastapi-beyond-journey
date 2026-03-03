from src.db.models import Users, PasswordResetOtp
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.auth.schemas import UserCreateModel,OtpCreateModel,PasswordResetRequestModel
from src.auth.utils import generate_password_hash
import random
from datetime import datetime , timedelta
from src.celery_tasks import send_email

OTP_EXPIRATION_MINUTES = 10

class UserService:
    async def get_user_by_email(self, email:str, session:AsyncSession):
        statement = select(Users).where(Users.email == email)
        result = await session.exec(statement)

        return result.first()


    async def user_exists(self, email, session:AsyncSession):
        is_exist = await self.get_user_by_email(email,session)

        return True if is_exist else False 

    
    async def create_user(self,user_data:UserCreateModel,session:AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = Users(
            **user_data_dict
        )

        new_user.password_hash = generate_password_hash(user_data_dict['password'])

        session.add(new_user);

        await session.commit()

        return new_user




    async def update_user(self, user:Users , user_data: dict,session:AsyncSession):

        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user


    async def create_password_reset_otp(
        self,
        email: str,
        session: AsyncSession
    ) -> None:
    
        user = await self.get_user_by_email(email, session)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Delete old OTPs
        statement = select(PasswordResetOtp).where(
            PasswordResetOtp.email == email
        )
        result = await session.exec(statement)
        old_otps = result.all()

        for otp in old_otps:
            await session.delete(otp)


        otp_code = str(random.randint(100000, 999999))

        otp_entry = PasswordResetOtp(
            email=email,
            otp=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)
        )

        session.add(otp_entry)
        await session.commit()

        subject = "Your Password Reset OTP"
        html = f"""
        <h1>Reset Your Password</h1>
        <p>Your OTP is:</p>
        <h2>{otp_code}</h2>
        <p>Expires in {OTP_EXPIRATION_MINUTES} minutes.</p>
        """
        send_email.delay(email, subject, html)

    async def set_reset_otp(self, user: Users, otp: str, expiry, session):
        user.reset_otp_hash = generate_passwd_hash(otp)
        user.reset_otp_expiry = expiry
        await session.commit()

    async def verify_reset_otp(self, user: Users, otp: str) -> bool:
        if not user.reset_otp_hash or not user.reset_otp_expiry:
            return False

        if datetime.utcnow() > user.reset_otp_expiry:
            return False

        return verify_password(otp, user.reset_otp_hash)

    async def clear_reset_otp(self, user: Users, session):
        user.reset_otp_hash = None
        user.reset_otp_expiry = None
        await session.commit()