import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta


def create_dummy_csv(has_timezone=False, has_duplicates=False, has_gaps=False):
    """Create a dummy CSV content in memory."""
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(24)]

    if has_gaps:
        # Remove the 12th hour
        dates.pop(12)

    if has_duplicates:
        # Duplicate the first hour
        dates.append(dates[0])

    values = [float(i) * 10.5 for i in range(len(dates))]

    df = pd.DataFrame({"timestamp": dates, "value": values})

    if has_timezone:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # Create CSV buffer
    buffer = BytesIO()
    # Using semicolon as requested in prompt "timestamp ; value"
    # Include header=True because the service expects/consumes a header
    df.to_csv(buffer, sep=";", index=False, header=True)
    buffer.seek(0)
    return buffer
