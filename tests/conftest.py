import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import hash_password


# In-memory SQLite for isolation
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ── Helper: create a user in the DB and return an auth token ──


def _create_user(db, email: str, password: str, role: Role, active: bool = True) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=f"Test {role.value.title()}",
        role=role,
        is_active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_token(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db):
    return _create_user(db, "admin@test.com", "Admin12345!", Role.admin)


@pytest.fixture()
def analyst_user(db):
    return _create_user(db, "analyst@test.com", "Analyst12345!", Role.analyst)


@pytest.fixture()
def viewer_user(db):
    return _create_user(db, "viewer@test.com", "Viewer12345!", Role.viewer)


@pytest.fixture()
def admin_token(client, admin_user):
    return _get_token(client, "admin@test.com", "Admin12345!")


@pytest.fixture()
def analyst_token(client, analyst_user):
    return _get_token(client, "analyst@test.com", "Analyst12345!")


@pytest.fixture()
def viewer_token(client, viewer_user):
    return _get_token(client, "viewer@test.com", "Viewer12345!")
