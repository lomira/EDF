import pytest
from src.backend.database.manager import DatabaseManager


@pytest.fixture
def test_db():
    """Create an in-memory DuckDB instance for testing."""
    db = DatabaseManager(":memory:")
    yield db
    db.close()
