from fastapi import FastAPI
from src.backend.api.ingestion import router as ingestion_router

app = FastAPI(title="EDF - Electricity Demand Forecasting")

# Include routers
app.include_router(ingestion_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to EDF API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
