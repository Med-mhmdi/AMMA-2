from fastapi import FastAPI

from app.api.routes import router
from app.database import Base, engine
from app.models.expense import Expense  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.budget import Budget  # noqa: F401
from shared.amma_observability import setup_observability


app = FastAPI(title="AMMA Expense Service")

Base.metadata.create_all(bind=engine)

app.include_router(router)
setup_observability(app, service_name="amma-expense-service")
