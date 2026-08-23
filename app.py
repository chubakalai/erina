import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Static File Server")

# Define directory paths
BASE_DIR = Path(__file__).resolve().parent
MAIN_DIR = BASE_DIR / "main"
BASEPICS_DIR = BASE_DIR / "basepics"

# Ensure directories exist
MAIN_DIR.mkdir(parents=True, exist_ok=True)
BASEPICS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Serve all .jpg files in basepics by path
# Mounts the basepics directory at /basepics endpoint
app.mount("/basepics", StaticFiles(directory=BASEPICS_DIR), name="basepics")


# 2. Serve all HTML files in main by name without extension
@app.get("/{page_name}")
async def serve_html_page(page_name: str):
    # Prevent directory traversal attacks
    if ".." in page_name or "/" in page_name or "\\" in page_name:
        raise HTTPException(status_code=400, detail="Invalid page request.")

    target_file = (MAIN_DIR / f"{page_name}.html").resolve()

    # Security check to ensure the resolved path stays within MAIN_DIR
    if not str(target_file).startswith(str(MAIN_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied.")

    if target_file.is_file():
        return FileResponse(target_file, media_type="text/html")

    raise HTTPException(status_code=404, detail="Page not found")


# Optional root handler mapping GET / to main/index.html
@app.get("/")
async def serve_index():
    index_file = MAIN_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Index page not found")
