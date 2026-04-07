"""
Ping-router – returnerer mock ping-resultater for én eller flere servere.

TODO: implement real measurement – erstatt mock_measurements.json med
ekte ICMP/TCP-ping mot faktiske IP-adresser via et agent-nettverk.
"""

import json
import pathlib
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(tags=["ping"])

_MOCK_PATH = pathlib.Path(__file__).parent.parent / "data" / "mock_measurements.json"


def _load_mock() -> dict:
    with open(_MOCK_PATH) as fh:
        return json.load(fh)


def _ping_status(ms: float, jitter: float, loss: float) -> str:
    if loss > 5 or ms > 200:
        return "bad"
    if loss > 1 or ms > 100:
        return "warn"
    if ms > 50:
        return "ok"
    return "good"


def _ping_score(ms: float, jitter: float, loss: float) -> int:
    """Score 0–100 – høyere er bedre."""
    score = 100
    score -= min(int(ms / 2), 50)
    score -= min(int(jitter * 3), 20)
    score -= min(int(loss * 10), 30)
    return max(0, score)


def _verdict(score: int) -> str:
    if score >= 85:
        return "Utmerket"
    if score >= 70:
        return "Bra"
    if score >= 50:
        return "OK"
    if score >= 30:
        return "Tregt"
    return "Dårlig"


def _verdict_long(server_id: str, score: int, ms: float) -> str:
    if score >= 85:
        return f"Forbindelsen til {server_id} er utmerket – {ms:.0f} ms latens vil du knapt merke."
    if score >= 70:
        return f"Bra forbindelse til {server_id} – {ms:.0f} ms er innenfor det akseptable."
    if score >= 50:
        return f"OK forbindelse til {server_id} – {ms:.0f} ms kan gi litt treghet i sanntidsspill."
    if score >= 30:
        return f"Treg forbindelse til {server_id} – {ms:.0f} ms vil gi merkbar forsinkelse."
    return f"Dårlig forbindelse til {server_id} – {ms:.0f} ms er for høyt for de fleste tjenester."


def _build_result(server_id: str, data: dict) -> dict:
    ms = data["ping_ms"]
    jitter = data["jitter_ms"]
    loss = data["packet_loss_pct"]
    score = _ping_score(ms, jitter, loss)
    return {
        "server_id": server_id,
        "ms": ms,
        "jitter_ms": jitter,
        "packet_loss_pct": loss,
        "status": _ping_status(ms, jitter, loss),
        "score": score,
        "verdict": _verdict(score),
        "verdict_long": _verdict_long(server_id, score, ms),
    }


def _category_score(results: list, server_ids: list) -> int:
    relevant = [r for r in results if r["server_id"] in server_ids]
    if not relevant:
        return 0
    return int(sum(r["score"] for r in relevant) / len(relevant))


@router.get("/ping/multi")
async def ping_multi(
    targets: str = Query(..., description="Kommaseparerte server-IDer"),
    source: str = Query("local", description="Kilde-ID"),
):
    """
    TODO: implement real measurement – kjør ekte ICMP ping fra agent.
    """
    mock = _load_mock()
    source_data = mock["sources"].get(source, mock["sources"]["local"])
    measurements = source_data["measurements"]

    target_list = [t.strip() for t in targets.split(",") if t.strip()]
    results = []
    for tid in target_list:
        data = measurements.get(tid, {"ping_ms": 999, "jitter_ms": 99, "packet_loss_pct": 100})
        results.append(_build_result(tid, data))

    gaming_ids  = ["steam", "valorant", "blizzard", "epic", "ea", "lol-euw", "psn", "xbox", "minecraft", "cs2"]
    stream_ids  = ["netflix", "youtube", "twitch", "spotify", "disney", "hbo", "vg", "nrk"]
    work_ids    = ["teams", "m365", "zoom", "gmeet", "slack", "webex", "github", "aws-euwest", "azure-westeu"]

    gaming_score    = _category_score(results, gaming_ids)
    streaming_score = _category_score(results, stream_ids)
    work_score      = _category_score(results, work_ids)

    measured_scores = [r["score"] for r in results]
    overall_score = int(sum(measured_scores) / len(measured_scores)) if measured_scores else 0

    best_result  = max(results, key=lambda r: r["score"]) if results else None
    worst_result = min(results, key=lambda r: r["score"]) if results else None

    return {
        "source": source,
        "results": results,
        "summary": {
            "gaming_score":    gaming_score or overall_score,
            "streaming_score": streaming_score or overall_score,
            "work_score":      work_score or overall_score,
            "overall_score":   overall_score,
            "best_server":     best_result["server_id"] if best_result else "",
            "worst_server":    worst_result["server_id"] if worst_result else "",
        },
    }


@router.get("/ping/single")
async def ping_single(
    target: str = Query(..., description="Server-ID"),
    source: str = Query("local", description="Kilde-ID"),
):
    """
    TODO: implement real measurement – kjør ekte ICMP ping fra agent.
    """
    mock = _load_mock()
    source_data = mock["sources"].get(source, mock["sources"]["local"])
    measurements = source_data["measurements"]

    data = measurements.get(target, {"ping_ms": 999, "jitter_ms": 99, "packet_loss_pct": 100})
    return {
        "source": source,
        "result": _build_result(target, data),
    }
