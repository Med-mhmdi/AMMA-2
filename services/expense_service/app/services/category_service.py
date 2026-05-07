from fastapi import HTTPException

from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(
        self,
        category_repository: CategoryRepository,
        expense_repository: ExpenseRepository,
    ):
        self.category_repository = category_repository
        self.expense_repository = expense_repository

    def create_category(self, user_id: int, payload: CategoryCreate):
        existing = self.category_repository.get_by_name(payload.name, user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Category already exists")

        return self.category_repository.create(user_id, payload.name)

    def list_categories(self, user_id: int):
        return self.category_repository.list_by_user(user_id)

    def update_category(self, category_id: int, user_id: int, payload: CategoryUpdate):
        category = self.category_repository.get_by_id(category_id, user_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        existing = self.category_repository.get_by_name(payload.name, user_id)
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail="Category already exists")

        category.name = payload.name
        return self.category_repository.save(category)

    def delete_category(self, category_id: int, user_id: int):
        category = self.category_repository.get_by_id(category_id, user_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        usage_count = self.expense_repository.count_by_category(category_id, user_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a category that is already used by expenses",
            )

        self.category_repository.delete(category)
        return {"message": "Category deleted successfully"}