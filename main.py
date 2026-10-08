from fastapi import FastAPI

app = FastAPI(title="Code Battle", version="0.1.0")


@app.get("/health", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    """Return a lightweight liveness response for Docker and local development."""

    return {"status": "ok"}
