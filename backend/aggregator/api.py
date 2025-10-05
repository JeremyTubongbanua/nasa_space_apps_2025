from __future__ import annotations

from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

if __name__ == "__main__" and __package__ is None:
    package_root = Path(__file__).resolve().parent
    if str(package_root) not in sys.path:
        sys.path.append(str(package_root))
    from openaq import router as openaq_router  # type: ignore
    from openmeteo import router as openmeteo_router  # type: ignore
else:
    from .openaq import router as openaq_router
    from .openmeteo import router as openmeteo_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openaq_router)
app.include_router(openmeteo_router)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
