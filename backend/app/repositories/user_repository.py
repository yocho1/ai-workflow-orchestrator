from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def create(self, db: Session, *, email: str, full_name: str, password_hash: str) -> User:
        user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            is_active=True,
            role="client",
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        return user
