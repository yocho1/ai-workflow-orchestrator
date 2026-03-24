from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    def ping_database(self, db: Session) -> bool:
        db.execute(text("SELECT 1"))
        return True
