from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, TokenPayload, UserRead


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def register(self, db: Session, *, email: str, full_name: str, password: str) -> AuthResponse:
        existing = self.user_repository.get_by_email(db, email)
        if existing is not None:
            raise ValueError("Email is already registered")

        user = self.user_repository.create(
            db,
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
        )
        db.commit()
        db.refresh(user)

        return self._auth_payload(user)

    def login(self, db: Session, *, email: str, password: str) -> AuthResponse:
        user = self.user_repository.get_by_email(db, email)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        return self._auth_payload(user)

    def me(self, user: User) -> UserRead:
        return UserRead.model_validate(user, from_attributes=True)

    def _auth_payload(self, user: User) -> AuthResponse:
        settings = get_settings()
        expires_minutes = settings.auth_access_token_exp_minutes
        token = create_access_token(subject=str(user.id), expires_minutes=expires_minutes)
        return AuthResponse(
            token=TokenPayload(
                access_token=token,
                token_type="bearer",
                expires_in=expires_minutes * 60,
            ),
            user=UserRead.model_validate(user, from_attributes=True),
        )
