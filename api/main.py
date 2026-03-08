from mangum import Mangum
from src import app  # import your FastAPI app from __init__.py

handler = Mangum(app)