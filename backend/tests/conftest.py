from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.main import app
from app.models.base import Base
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine) -> Generator[TestClient, None, None]:
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def logged_in_user(client: TestClient, db: Session):
    """Create and login a test user, return user info and auth token."""
    # Create user in database
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        password_hash=hash_password("testpassword123"),
        is_active=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()

    return {
        "user_id": user.id,
        "email": user.email,
        "token": data["data"]["token"]["access_token"],
    }


@pytest.fixture
def test_document(logged_in_user: dict, db: Session):
    """Create a test document for the logged-in user."""
    document = Document(
        user_id=logged_in_user["user_id"],
        filename="test_invoice.pdf",
        content_type="application/pdf",
        storage_path="/uploads/test_invoice.pdf",
        extracted_text="This is a test invoice with amount $100.00",
        processing_status=DocumentStatus.UPLOADED,
        document_type=None,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@pytest.fixture
def test_document_other_user(db: Session):
    """Create a test document for a different user."""
    # Create another user
    other_user = User(
        email="otheruser@example.com",
        full_name="Other User",
        password_hash=hash_password("otherpassword123"),
        is_active=True,
        role="user",
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    # Create document for other user
    document = Document(
        user_id=other_user.id,
        filename="other_invoice.pdf",
        content_type="application/pdf",
        storage_path="/uploads/other_invoice.pdf",
        extracted_text="This is another invoice",
        processing_status=DocumentStatus.UPLOADED,
        document_type=None,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
