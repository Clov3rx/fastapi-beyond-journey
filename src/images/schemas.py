from pydantic import BaseModel,Field, EmailStr
import uuid 
from typing import List
from datetime import datetime



class ImageUploadModel(BaseModel):
    filename: str
    data: bytes
    owner_id: uuid.UUID


class Image_Model(BaseModel):
    id: int 
    filename: str
    owner_id: uuid.UUID