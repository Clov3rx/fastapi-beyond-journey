
>Steps 
# 
__init__.py 
models.py -> create models that will store in db 
routers.py -> routing based on services methods 
schema.py -> structure to apply http methods 
services.py -> logic for appling routing 


> DataBase Migration
alembic init -t async migrations 
#
alembic revision --autogenerate -m "flag to know what u did"
##
alembic upgrade head 
###
alembic downgrade head 

> celery
#
celery -A src.celery_tasks.c_app worker --loglevel=info# fastapi-beyond-journey
