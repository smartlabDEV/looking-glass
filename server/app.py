import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from routers import traceroute, ping, servers, sources, ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("looking-glass")

app = FastAPI(
    title="Looking Glass for vanlig folk",
    description="Nett-reise visualisering og AI rute-optimalisering",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers.router,    prefix="/api")
app.include_router(sources.router,    prefix="/api")
app.include_router(traceroute.router, prefix="/api")
app.include_router(ping.router,       prefix="/api")
app.include_router(ai.router,         prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html")


@app.on_event("startup")
async def startup_event():
    banner = r"""
  _              _    _               ____ _
 | |    ___  ___| | _(_)_ __   __ _  / ___| | __ _ ___ ___
 | |   / _ \/ _ \ |/ / | '_ \ / _` || |  | |/ _` / __/ __|
 | |__| (_) |  __/   <| | | | | (_| || |__| | (_| \__ \__ \
 |_____\___/ \___|_|\_\_|_| |_|\__, | \____|_|\__,_|___/___/
                                |___/
    Looking Glass for vanlig folk  +  AI Route Optimizer
    """
    for line in banner.splitlines():
        logger.info(line)
    logger.info("Server klar på http://0.0.0.0:8000")
