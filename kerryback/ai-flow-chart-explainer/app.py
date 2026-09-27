from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

HERE = Path(__file__).resolve().parent
app = FastAPI(title="AI Flow Chart Explainer", docs_url=None, redoc_url=None)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(HERE / "index.html", media_type="text/html")


@app.get("/AI Flow chart Tool.png", include_in_schema=False)
@app.get("/chart.png", include_in_schema=False)
def chart() -> FileResponse:
    return FileResponse(HERE / "AI Flow chart Tool.png", media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8008)
