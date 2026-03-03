from src.db.models import Images
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.images.schemas import ImageUploadModel
from datetime import datetime , timedelta


class ImageService:

    async def upload_image(self,image_data:ImageUploadModel,session:AsyncSession):
        image_data_dict = image_data.model_dump()

        new_image = Images(
            **image_data_dict
        )

        session.add(new_image);

        await session.commit()

        return new_image
