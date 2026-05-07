from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.database import Base, engine

# Import models so SQLAlchemy can create tables.
from app.models.user import User  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)