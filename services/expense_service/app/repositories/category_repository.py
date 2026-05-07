from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, name: str) -> Category:
        category = Category(user_id=user_id, name=name)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_by_user(self, user_id: int) -> list[Category]:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.name.asc())
            .all()
        )

    def get_by_id(self, category_id: int, user_id: int) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )

    def get_by_name(self, name: str, user_id: int) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.name == name, Category.user_id == user_id)
            .first()
        )

    def save(self, category: Category) -> Category:
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()