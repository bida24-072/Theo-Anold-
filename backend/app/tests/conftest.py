import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.security import hash_password
from app.models import User, Gate

# In-memory SQLite for fast tests
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    db.add(User(username="guard", name="Test Guard",
                hashed_password=hash_password("guard123"), role="guard"))
    db.add(Gate(name="Entry A", direction="in", kind="student_entry"))
    db.add(Gate(name="Exit",    direction="out", kind="student_exit"))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    def override():
        db = TestingSession()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
