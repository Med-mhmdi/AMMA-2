from fastapi import FastAPI

from app.api.routes import router
from app.database import Base, engine

from app.models.expense import Expense
from app.models.category import Category
from app.models.budget import Budget

app = FastAPI(title="AMMA Expense Service")

Base.metadata.create_all(bind=engine)

app.include_router(router)