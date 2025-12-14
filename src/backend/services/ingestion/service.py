from typing import Dict, Any
from src.backend.database.manager import db_manager
from src.backend.pydantic_models.ingestion import IngestionConfig


class IngestionError(Exception):
    """Custom exception for ingestion errors."""

    pass


def ingest_csv_timeseries(config: IngestionConfig) -> Dict[str, Any]:
    """
    Ingest a CSV timeseries file into the database.

    Args:
        config: Configuration for the ingestion (name, frequency, file_buffer).
                Validation happens upon config instantiation.

    Returns:
        Dictionary containing ingestion statistics.{status, rows_inserted, message}

    Raises:
        IngestionError: If validation fails.
    """
    try:
        # 1. Domain Logic (Already handled in config)
        df_clean = config.dataframe

        # 2. Persistence Logic (Database)
        conn = db_manager.get_connection()

        # Add metadata columns
        df_clean["series_name"] = config.name
        df_clean["frequency"] = config.frequency.value

        # Register dataframe as a view for easy SQL insertion
        conn.register("temp_ingest_df", df_clean)

        insert_query = """
        INSERT INTO master_series (series_name, timestamp, value, frequency)
        SELECT series_name, timestamp, value, frequency FROM temp_ingest_df
        ON CONFLICT (series_name, timestamp) DO UPDATE SET
            value = EXCLUDED.value,
            frequency = EXCLUDED.frequency,
            ingested_at = now()
        """

        conn.execute(insert_query)
        conn.unregister("temp_ingest_df")

        return {
            "status": "success",
            "rows_inserted": len(df_clean),
            "message": f"Successfully ingested {len(df_clean)} rows.",
        }

    except IngestionError:
        raise
    except Exception as e:
        raise IngestionError(f"Unexpected error during ingestion: {str(e)}")
