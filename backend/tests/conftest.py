import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_reviewmind.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-testing-32-chars-long")
if not os.environ.get("HINDSIGHT_BASE_URL"):
    os.environ["HINDSIGHT_BASE_URL"] = "https://api.hindsight.vectorize.io"

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_reviewmind.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_reviewmind.db"):
        try:
            os.remove("./test_reviewmind.db")
        except Exception:
            pass

@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
