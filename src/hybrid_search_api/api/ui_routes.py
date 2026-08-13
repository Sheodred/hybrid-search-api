from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

_INDEX_HTML = Path(__file__).resolve().parent.parent / "static" / "index.html"

router = APIRouter()


@router.get("/", include_in_schema=False)
def search_ui() -> FileResponse:
    return FileResponse(_INDEX_HTML)
