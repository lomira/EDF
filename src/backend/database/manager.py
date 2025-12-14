import duckdb
from pathlib import Path
from src.backend.config import settings


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.db_path
        self._ensure_data_dir()
        self.conn = duckdb.connect(self.db_path)
        self._init_schema()

    def _ensure_data_dir(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize the database schema."""
        # master_series table to store all time series data
        # We use a composite primary key to prevent duplicate timestamps for the same series
        query = """
        CREATE TABLE IF NOT EXISTS master_series (
            series_name VARCHAR,
            timestamp TIMESTAMP,
            value DOUBLE,
            frequency VARCHAR,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (series_name, timestamp)
        );
        """
        self.conn.execute(query)

    def get_connection(self):
        """Return the active DuckDB connection."""
        return self.conn

    def close(self):
        """Close the database connection."""
        self.conn.close()


# Global instance for easy access
db_manager = DatabaseManager()
