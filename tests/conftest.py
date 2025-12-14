import pytest
from src.backend.database.manager import DatabaseManager
from src.backend.config import settings


@pytest.fixture
def test_db():
    """Create an in-memory DuckDB instance for testing."""
    # Override settings for testing if needed, though we pass explicit path here
    original_db_path = settings.db_path
    settings.db_path = ":memory:"

    db = DatabaseManager(":memory:")
    yield db
    db.close()

    # Restore original setting
    settings.db_path = original_db_path
