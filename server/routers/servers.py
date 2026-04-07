import json
import pathlib
from fastapi import APIRouter

router = APIRouter(tags=["servers"])

_DATA_PATH = pathlib.Path(__file__).parent.parent / "data" / "servers.json"


@router.get("/servers")
async def get_servers():
    """Returnerer alle servere gruppert i kategorier."""
    with open(_DATA_PATH) as fh:
        return json.load(fh)
