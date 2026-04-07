"""
Hent nåværende nettverkstilstand fra:
- TimescaleDB (NetFlow-data fra NE8000)
- SmokePing RRD (latency/jitter historikk)

Returnerer numpy array klar for PPO-agenten.
"""

import datetime
import logging
import os

import numpy as np

logger = logging.getLogger(__name__)

# Konfigurasjon leses fra miljøvariabler — ikke hardkode credentials i kildekoden.
# Sett disse i docker-compose.yml eller .env:
#   SMOKEPING_RRD_TELIA=/smokeping/telia/steam.rrd
#   SMOKEPING_RRD_NIX=/smokeping/nix/steam.rrd
#   DB_DSN=postgresql://user:pass@db:5432/lookingglass
SMOKEPING_RRD_TELIA = os.environ.get(
    "SMOKEPING_RRD_TELIA", "/smokeping/telia/steam.rrd"
)
SMOKEPING_RRD_NIX = os.environ.get("SMOKEPING_RRD_NIX", "/smokeping/nix/steam.rrd")
DB_DSN = os.environ.get("DB_DSN", "")  # TODO: sett DB_DSN i miljøvariabler


async def get_current_state() -> np.ndarray:
    """
    Hent state for RL-agenten.
    Returnerer numpy array med 12 features.
    """

    # SmokePing data
    nix_latency = _get_smokeping_avg(SMOKEPING_RRD_NIX, seconds=3600)
    telia_latency = _get_smokeping_avg(SMOKEPING_RRD_TELIA, seconds=3600)
    nix_loss = _get_smokeping_loss(SMOKEPING_RRD_NIX, seconds=3600)
    telia_loss = _get_smokeping_loss(SMOKEPING_RRD_TELIA, seconds=3600)

    # Latency trend (siste 30 min vs 30 min siden)
    telia_now = _get_smokeping_avg(SMOKEPING_RRD_TELIA, seconds=1800)
    telia_prev = _get_smokeping_avg(SMOKEPING_RRD_TELIA, seconds=3600, offset=1800)
    latency_delta = telia_now - telia_prev

    # NetFlow fra TimescaleDB
    # TODO: Koble til din pmacct/NetFlow DB
    transit_gbps = 2.5    # TODO: hent fra DB
    nix_gbps = 1.2        # TODO: hent fra DB
    total_gbps = transit_gbps + nix_gbps
    transit_cost = 25.0   # TODO: din faktiske kr/Mbit-pris
    nix_util = 45.0       # TODO: hent fra NE8000 via Nornir/SNMP

    now = datetime.datetime.now()

    return np.array(
        [
            transit_cost,
            nix_util,
            telia_latency,
            nix_latency,
            total_gbps,
            transit_gbps,
            nix_gbps,
            float(now.hour),
            float(now.weekday()),
            latency_delta,
            nix_loss,
            telia_loss,
        ],
        dtype=np.float32,
    )


def _get_smokeping_avg(rrd_path: str, seconds: int, offset: int = 0) -> float:
    """Les gjennomsnittlig latency fra SmokePing RRD"""
    try:
        import rrdtool

        end = int(datetime.datetime.now().timestamp()) - offset
        start = end - seconds
        result = rrdtool.fetch(rrd_path, "AVERAGE", "-s", str(start), "-e", str(end))
        values = [v[0] for v in result[2] if v[0] is not None]
        return float(np.mean(values)) * 1000 if values else 20.0  # ms
    except Exception as e:
        logger.warning(f"SmokePing RRD feil: {e}")
        return 20.0  # fallback


def _get_smokeping_loss(rrd_path: str, seconds: int) -> float:
    """Les pakketap fra SmokePing RRD"""
    try:
        import rrdtool

        end = int(datetime.datetime.now().timestamp())
        start = end - seconds
        result = rrdtool.fetch(rrd_path, "AVERAGE", "-s", str(start), "-e", str(end))
        values = [v[1] for v in result[2] if v[1] is not None]
        return float(np.mean(values)) * 100 if values else 0.0  # pct
    except Exception as e:
        logger.warning(f"SmokePing loss RRD feil: {e}")
        return 0.0
