from fastapi.testclient import TestClient
from unittest.mock import patch
from src.main_app import app
from tests.helpers import create_dummy_csv

client = TestClient(app)


def test_upload_csv_success():
    """Test successful CSV upload via API."""
    # Mock the service function to avoid actual DB/File operations
    with patch("src.backend.api.ingestion.ingest_csv_timeseries") as mock_ingest:
        mock_ingest.return_value = {
            "status": "success",
            "rows_inserted": 24,
            "message": "Success",
        }

        # Create dummy file content using helper
        csv_buffer = create_dummy_csv()
        file_content = csv_buffer.getvalue()

        response = client.post(
            "/ingest/csv",
            files={"file": ("test.csv", file_content, "text/csv")},
            data={"name": "test_series", "frequency": "h"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_ingest.assert_called_once()


def test_upload_csv_validation_error():
    """Test API handles validation errors from service."""
    # We don't need to mock side_effect because IngestionConfig validation happens before service call
    with patch("src.backend.api.ingestion.ingest_csv_timeseries") as mock_ingest:
        file_content = b"invalid_content"

        response = client.post(
            "/ingest/csv",
            files={"file": ("test.csv", file_content, "text/csv")},
            data={"name": "test_series", "frequency": "h"},
        )

        assert response.status_code == 400
        # The error message comes from validation failure (either read or structure)
        detail = response.json()["detail"]
        # Service should NOT be called because validation failed earlier
        mock_ingest.assert_not_called()
        assert (
            "Failed to read CSV file" in detail
            or "CSV must have exactly 2 columns" in detail
        )


def test_upload_csv_missing_params():
    """Test API rejects missing parameters."""
    csv_buffer = create_dummy_csv()
    file_content = csv_buffer.getvalue()

    # Missing frequency
    response = client.post(
        "/ingest/csv",
        files={"file": ("test.csv", file_content, "text/csv")},
        data={"name": "test_series"},
    )

    assert response.status_code == 422  # Validation Error
