from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Static File Server")

BASE_DIR = Path(__file__).resolve().parent
MAIN_DIR = BASE_DIR
BASEPICS_DIR = BASE_DIR / "basepics"

MAIN_DIR.mkdir(parents=True, exist_ok=True)
BASEPICS_DIR.mkdir(parents=True, exist_ok=True)

# Static file server endpoint
app.mount("/basepics", StaticFiles(directory=BASEPICS_DIR), name="basepics")


# API Endpoint to list image filenames
@app.get("/api/basepics")
async def get_basepics():
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    return [
        f.name
        for f in BASEPICS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]


@app.get("/{page_name}")
async def serve_html_page(page_name: str):
    if ".." in page_name or "/" in page_name or "\\" in page_name:
        raise HTTPException(status_code=400, detail="Invalid page request.")

    target_file = (MAIN_DIR / f"{page_name}.html").resolve()

    if not str(target_file).startswith(str(MAIN_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied.")

    if target_file.is_file():
        return FileResponse(target_file, media_type="text/html")

    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/")
async def serve_index():
    index_file = MAIN_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Index page not found")
