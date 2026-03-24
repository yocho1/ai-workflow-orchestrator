from sqlalchemy.orm import Session

from app.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, repository: HealthRepository | None = None) -> None:
        self.repository = repository or HealthRepository()

    def get_health_status(self, db: Session) -> dict[str, str | bool]:
        database_ok = self.repository.ping_database(db)
        return {
            "status": "ok",
            "database": "ok" if database_ok else "unavailable",
        }
