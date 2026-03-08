from fastapi import FastAPI 
#from src.Book.routers import book_router
from contextlib import asynccontextmanager 
from src.db.main import init_db
from src.auth.routers import auth_router
from src.images.routers import image_router
from .errors import register_all_errors
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def life_span(app:FastAPI):
    print(f"Server is starting ... ")
    await init_db()
    yield 
    print(f"Server has been stopped")



version = "v1"

app = FastAPI(
    title="Medical Image",
    version=version,
    lifespan=life_span
)

register_all_errors(app)

#app.include_router(book_router,prefix=f"/api/{version}/books")
app.include_router(auth_router,prefix=f"/api/{version}/auth")
app.include_router(image_router,prefix=f"/api/{version}/upload")