from fastapi import APIRouter,Depends ,status,UploadFile, File , Form
from src.images.schemas import ImageUploadModel , Image_Model
from src.images.service import ImageService
from fastapi.exceptions import HTTPException
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse 
import uuid
from src.auth.dependencies import get_current_user
from src.db.models import Users,Images
from sqlmodel import select
from fastapi.responses import StreamingResponse
from io import BytesIO


image_router = APIRouter()

image_service = ImageService()

from typing import List
from fastapi import UploadFile, File, Depends

@image_router.post("/upload_images", response_model=List[Image_Model])
async def upload_images(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    saved_images = []

    for file in files:
        data = await file.read()  # Read image bytes

        # Create Images object
        image = Images(
            filename=file.filename,
            data=data,
            owner_id=current_user.uid
        )

        # Add to session and commit
        session.add(image)
        await session.commit()
        await session.refresh(image)  # Refresh to get ID

        saved_images.append(image)

    return saved_images



@image_router.get("/image/{image_id}")
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_session),
    user: Users = Depends(get_current_user)
):
    result = await db.exec(select(Images).where(Images.id == image_id))
    image = result.first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.owner_id != user.uid:
        raise HTTPException(status_code=403, detail="Not allowed to access this image")

    return StreamingResponse(BytesIO(image.data), media_type="image/jpeg")
 