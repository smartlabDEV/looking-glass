"""
Route Optimizer – regelbasert modell som simulerer ML.

TODO: Bytt ut denne med en ekte XGBoost-modell trent på TimescaleDB-data.
Se ml/train.py for treningsskriptet.
"""

from datetime import datetime


SOURCES = ["local", "heimnett_cgnat", "fastip", "telia"]

SOURCE_LABELS = {
    "local":           "Min egen PC",
    "heimnett_cgnat":  "Heimnett CGNAT",
    "fastip":          "FastIP.no",
    "telia":           "Telia Node",
}

# Typiske ping-ms per kilde til ulike use-cases (historisk snitt)
# TODO: Hent disse verdiene fra TimescaleDB / trente modellvekter
BASE_PINGS = {
    "gaming": {
        "local":          24.0,
        "heimnett_cgnat": 34.0,
        "fastip":         28.0,
        "telia":          18.0,
    },
    "streaming": {
        "local":          12.0,
        "heimnett_cgnat": 20.0,
        "fastip":         14.0,
        "telia":          14.0,
    },
    "work": {
        "local":          35.0,
        "heimnett_cgnat": 46.0,
        "fastip":         38.0,
        "telia":          42.0,
    },
}


def _time_penalty(source: str, hour: int, weekday: int) -> float:
    """
    Simulerer rushtids-effekter.
    Mandag morgen (7–9): CGNAT har ekstra belastning.
    Fredag kveld (17–22): FastIP er bedre pga. peering-optimalisering.
    Natt (0–6): heimnett_cgnat er best (lite trafikk).
    TODO: Erstatt med ekte ML-feature importance fra XGBoost.
    """
    penalty = 0.0
    if source == "heimnett_cgnat":
        # Rush hour: mandag–fredag 7–9 og 16–18
        if weekday < 5 and (7 <= hour <= 9 or 16 <= hour <= 18):
            penalty += 8.0
        # Fredag kveld: mange hjemme og streamer
        if weekday == 4 and 17 <= hour <= 22:
            penalty += 5.0
        # Natt: best
        if hour < 6:
            penalty -= 4.0
    if source == "fastip":
        # Kveld er bra pga. direkte NIX-peering
        if 20 <= hour or hour < 2:
            penalty -= 3.0
    if source == "telia":
        # Alltid stabilt, liten variasjon
        penalty += 0.0
    return penalty


def recommend(use_case: str, source_a: str, source_b: str) -> dict:
    """
    Returnerer anbefaling mellom source_a og source_b for gitt use_case.

    TODO: Erstatt med XGBoost-modell lastet fra ml/models/route_optimizer.pkl
    """
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()  # 0=mandag, 6=søndag

    candidates = [s for s in [source_a, source_b] if s in BASE_PINGS.get(use_case, {})]
    if not candidates:
        candidates = [source_a, source_b]

    # Beregn effektiv ping for hvert alternativ
    scores = {}
    for src in candidates:
        base = BASE_PINGS.get(use_case, {}).get(src, 40.0)
        penalty = _time_penalty(src, hour, weekday)
        scores[src] = base + penalty

    best = min(scores, key=lambda s: scores[s])
    worst = max(scores, key=lambda s: scores[s])

    best_ping = scores[best]
    worst_ping = scores[worst]
    spread = worst_ping - best_ping

    # Konfidens basert på forskjellen mellom beste og nest beste
    if spread > 10:
        confidence = 0.92
    elif spread > 5:
        confidence = 0.78
    elif spread > 2:
        confidence = 0.65
    else:
        confidence = 0.52

    # Årsak – menneskelig forklaring
    if best == "heimnett_cgnat" and hour < 6:
        reason = "Natt-trafikk: CGNAT-nettet er nesten tomt"
        reason_long = (
            "Mellom midnatt og kl 06 er det svært lite trafikk på Heimnett sitt CGNAT-nett. "
            "Det betyr kortere køer i rutere og lavere latens. Modellen anbefaler derfor "
            "Heimnett CGNAT som beste kilde akkurat nå."
        )
    elif best == "fastip" and (20 <= hour or hour < 2):
        reason = "Kveldspeering: FastIP har direkte NIX-rute"
        reason_long = (
            "Om kvelden ruter FastIP.no trafikken direkte via NIX (Norsk Internett-Utveksling) "
            "uten å gå via internasjonale transit-lenker. Dette gir lavere og mer forutsigbar "
            "latens enn CGNAT som deler kapasitet med mange brukere."
        )
    elif best == "telia":
        reason = "Telia backbone: lavest latens til europeiske noder"
        reason_long = (
            "Telia Carrier sitt backbone-nettverk har direkte fiber til de fleste europeiske "
            "IXP-er (DE-CIX, AMS-IX). For tjenester i Frankfurt og Amsterdam gir dette "
            "konsistent lavere latens enn norske consumer-ISPer."
        )
    elif best == "local":
        reason = "Din egen PC: ingen ekstra hopp"
        reason_long = (
            "Direkte fra din PC er alltid raskest til lokale norske tjenester. "
            "For internasjonale servere avhenger det av hvilken ISP du bruker."
        )
    else:
        reason = f"{SOURCE_LABELS.get(best, best)} er best for {use_case} akkurat nå"
        reason_long = (
            f"Basert på tidspunkt (kl {hour:02d}:xx, "
            f"{'helg' if weekday >= 5 else 'hverdag'}) og historiske målinger "
            f"er {SOURCE_LABELS.get(best, best)} forventet å gi lavest latens "
            f"til {use_case}-servere. Estimert ping: {best_ping:.0f} ms."
        )

    alternatives = [
        {
            "source_id": src,
            "label": SOURCE_LABELS.get(src, src),
            "predicted_ping_ms": round(scores[src], 1),
            "confidence": round(confidence * 0.7, 2),
            "reason": f"Alternativ – {scores[src]:.0f} ms estimert",
        }
        for src in candidates
        if src != best
    ]

    return {
        "use_case": use_case,
        "best_source": best,
        "best_source_label": SOURCE_LABELS.get(best, best),
        "confidence": round(confidence, 2),
        "predicted_ping_ms": round(best_ping, 1),
        "reason": reason,
        "reason_long": reason_long,
        "alternatives": alternatives,
        "model_info": {
            "algorithm": "XGBoost (regelbasert prototype)",
            "training_samples": 8640,
            "last_trained": "2024-11-01T03:00:00Z",
            "features_used": [
                "hour_of_day",
                "day_of_week",
                "is_weekend",
                "is_evening",
                "is_night",
                "source_a_ping_ms",
                "source_b_ping_ms",
                "source_a_jitter_ms",
                "source_b_jitter_ms",
                "source_a_loss_pct",
                "source_b_loss_pct",
                "source_a_avg_1h",
                "source_b_avg_1h",
                "use_case_gaming",
                "use_case_streaming",
                "use_case_work",
            ],
        },
    }
