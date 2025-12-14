from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator
import pandas as pd
from typing import BinaryIO, Union
from tempfile import SpooledTemporaryFile
from io import BytesIO


class Frequency(str, Enum):
    HOURLY = "h"
    DAILY = "d"
    MONTHLY = "MS"


class IngestionConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., min_length=1, description="Name of the time series")
    frequency: Frequency = Field(..., description="Frequency of the time series")
    file_buffer: Union[BinaryIO, SpooledTemporaryFile, BytesIO] = Field(
        ..., description="CSV file buffer"
    )
    dataframe: pd.DataFrame = Field(
        default=pd.DataFrame(), init=False, description="Processed DataFrame"
    )

    @model_validator(mode="after")
    def process_file(self) -> "IngestionConfig":
        """
        Read, validate and clean the CSV file upon initialization.
        """
        try:
            # Reset buffer position just in case
            if hasattr(self.file_buffer, "seek"):
                self.file_buffer.seek(0)

            df = pd.read_csv(
                self.file_buffer, sep=None, engine="python", encoding="utf-8"
            )
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

        if len(df.columns) != 2:
            raise ValueError(
                f"CSV must have exactly 2 columns. Found {len(df.columns)}: {df.columns.tolist()}"
            )

        df.columns = ["timestamp", "value"]

        # Validations
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        except Exception as e:
            raise ValueError(f"Column 1 must be a valid timestamp. Error: {str(e)}")

        try:
            df["value"] = pd.to_numeric(df["value"])
        except Exception as e:
            raise ValueError(f"Column 2 must be numeric. Error: {str(e)}")

        if df["timestamp"].dt.tz is not None:
            raise ValueError(
                "Timestamps must be timezone-naive (no timezone info allowed)."
            )

        df = df.sort_values("timestamp")

        duplicates = df[df.duplicated(subset=["timestamp"], keep=False)]
        if len(duplicates) > 0:
            raise ValueError(
                f"Found {len(duplicates)} duplicate timestamps. Please ensure all timestamps are unique."
            )

        if not df.empty:
            # Gaps
            expected_range = pd.date_range(
                start=df["timestamp"].min(),
                end=df["timestamp"].max(),
                freq=self.frequency.value,
            )

            actual_timestamps = set(df["timestamp"])
            expected_timestamps = set(expected_range)
            missing_timestamps = expected_timestamps - actual_timestamps
            num_gaps = len(missing_timestamps)

            if num_gaps > 0:
                raise ValueError(
                    f"Found {num_gaps} missing timestamps (gaps). Please ensure the time series is continuous."
                )

        self.dataframe = df
        return self
