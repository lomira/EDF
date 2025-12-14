import pytest
from unittest.mock import patch
from src.backend.services.ingestion.service import ingest_csv_timeseries
from src.backend.pydantic_models.ingestion import IngestionConfig, Frequency
from tests.helpers import create_dummy_csv

# --- Tests ---


def test_valid_ingestion(test_db):
    """Test successful ingestion of a valid CSV."""
    # Patch the global db_manager in the service module to use our in-memory test_db
    with patch("src.backend.services.ingestion.service.db_manager", test_db):
        csv_file = create_dummy_csv()
        config = IngestionConfig(
            name="test_load_hourly", frequency=Frequency.HOURLY, file_buffer=csv_file
        )

        result = ingest_csv_timeseries(config)

        assert result["status"] == "success"
        assert result["rows_inserted"] == 24

        # Verify DB content
        conn = test_db.get_connection()
        count = conn.execute(
            "SELECT count(*) FROM master_series WHERE series_name='test_load_hourly'"
        ).fetchone()[0]
        assert count == 24


def test_timezone_rejection():
    """Test that CSVs with timezone-aware timestamps are rejected."""
    csv_file = create_dummy_csv(has_timezone=True)

    # Validation happens at config instantiation now, raising ValueError
    with pytest.raises(ValueError, match="Timestamps must be timezone-naive"):
        IngestionConfig(
            name="test_tz_fail", frequency=Frequency.HOURLY, file_buffer=csv_file
        )


def test_duplicates_rejection(test_db):
    """Test that duplicates raise an error."""
    csv_file = create_dummy_csv(has_duplicates=True)

    with pytest.raises(ValueError, match="duplicate timestamps"):
        IngestionConfig(
            name="test_dupes", frequency=Frequency.HOURLY, file_buffer=csv_file
        )


def test_gaps_rejection(test_db):
    """Test that gaps raise an error."""
    csv_file = create_dummy_csv(has_gaps=True)

    with pytest.raises(ValueError, match="missing timestamps"):
        IngestionConfig(
            name="test_gaps", frequency=Frequency.HOURLY, file_buffer=csv_file
        )
