from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.database import Base, engine
from app.models.user import User  # noqa: F401
from shared.amma_observability import setup_observability


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)
setup_observability(app, service_name="amma-auth-service")
