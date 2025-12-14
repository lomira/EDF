from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Annotated
from src.backend.services.ingestion.service import ingest_csv_timeseries, IngestionError
from src.backend.pydantic_models.ingestion import IngestionConfig, Frequency

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/csv")
async def upload_csv(
    file: Annotated[
        UploadFile, File(description="CSV file with columns: timestamp; value")
    ],
    name: Annotated[str, Form(description="Name of the time series")],
    frequency: Annotated[
        Frequency, Form(description="Frequency of the time series (h, D, ME)")
    ],
):
    """
    Upload and ingest a CSV time series file.
    """
    try:
        config = IngestionConfig(name=name, frequency=frequency, file_buffer=file.file)
        result = ingest_csv_timeseries(config)
        return result

    except (ValueError, IngestionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
