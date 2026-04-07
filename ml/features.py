"""
features.py – Feature-ekstraksjon for Looking Glass AI Route Optimizer

Dette modulen konverterer rå nettverksmålinger og tidsinformasjon
til et feature-vektor som XGBoost-modellen kan lære av.

Forfattet med norske kommentarer for å gjøre AI-pipelinen tilgjengelig.
"""

from datetime import datetime
from typing import Optional
import math


def extract_time_features(dt: Optional[datetime] = None) -> dict:
    """
    Trekker ut tidspunkts-baserte features.

    Tidspunkt på dagen er en av de viktigste features fordi:
    - Mandag morgen: bedrifter starter, CGNAT-nett overbelastet
    - Fredag kveld: mange hjemme og streamer, kødannelse
    - Natt: lite trafikk, lavere latens
    - Helg: variabelt, men ofte bra på dagtid
    """
    if dt is None:
        dt = datetime.now()

    hour    = dt.hour
    weekday = dt.weekday()  # 0=mandag, 6=søndag

    # Er det kveld? (Definert som 18-23)
    is_evening = 1 if 18 <= hour <= 23 else 0

    # Er det natt? (Definert som 0-6)
    is_night = 1 if hour < 6 else 0

    # Er det rush-tid? (7-9 og 16-18 på hverdager)
    is_rush = 1 if (weekday < 5 and (7 <= hour <= 9 or 16 <= hour <= 18)) else 0

    return {
        "hour_of_day":  hour,
        "day_of_week":  weekday,
        "is_weekend":   1 if weekday >= 5 else 0,
        "is_evening":   is_evening,
        "is_night":     is_night,
        "is_rush_hour": is_rush,
        # Sykliske features – hjelper modellen forstå at time 23 er nær time 0
        "hour_sin":     round(math.sin(2 * math.pi * hour / 24), 4),
        "hour_cos":     round(math.cos(2 * math.pi * hour / 24), 4),
        "day_sin":      round(math.sin(2 * math.pi * weekday / 7), 4),
        "day_cos":      round(math.cos(2 * math.pi * weekday / 7), 4),
    }


def extract_measurement_features(
    ping_ms: float,
    jitter_ms: float,
    packet_loss_pct: float,
    avg_1h_ms: Optional[float] = None,
    avg_24h_ms: Optional[float] = None,
) -> dict:
    """
    Trekker ut nettverkskvalitets-features fra en enkelt kilde.

    - ping_ms: øyeblikkelig latens
    - jitter_ms: variasjon i latens (viktig for video og gaming)
    - packet_loss_pct: prosentandel tapte pakker
    - avg_1h_ms: 1-times gjennomsnitt (fra TimescaleDB)
    - avg_24h_ms: 24-timers gjennomsnitt

    TODO: Hent avg_1h og avg_24h fra TimescaleDB time_bucket query.
    """

    # Jitter-ratio: høy ratio betyr ustabilt nett
    jitter_ratio = round(jitter_ms / max(ping_ms, 1), 4)

    # Er det tap? Pakketap er svært negativt for gaming og video
    has_loss = 1 if packet_loss_pct > 0 else 0

    # Avvik fra historisk snitt (indikerer om noe er unormalt)
    drift_1h  = round(ping_ms - avg_1h_ms,  2) if avg_1h_ms  is not None else 0.0
    drift_24h = round(ping_ms - avg_24h_ms, 2) if avg_24h_ms is not None else 0.0

    return {
        "ping_ms":         ping_ms,
        "jitter_ms":       jitter_ms,
        "packet_loss_pct": packet_loss_pct,
        "jitter_ratio":    jitter_ratio,
        "has_loss":        has_loss,
        "avg_1h_ms":       avg_1h_ms  if avg_1h_ms  is not None else ping_ms,
        "avg_24h_ms":      avg_24h_ms if avg_24h_ms is not None else ping_ms,
        "drift_from_1h":   drift_1h,
        "drift_from_24h":  drift_24h,
    }


def extract_use_case_features(use_case: str) -> dict:
    """
    One-hot encoding av brukstilfelle.

    Hvert brukstilfelle har ulike krav:
    - Gaming: krever svært lav latens (<30ms), lav jitter
    - Streaming: tåler høyere latens, men ikke pakketap
    - Work: middels krav, men jitter påvirker videomøter
    """
    return {
        "use_case_gaming":    1 if use_case == "gaming"    else 0,
        "use_case_streaming": 1 if use_case == "streaming" else 0,
        "use_case_work":      1 if use_case == "work"      else 0,
    }


def build_feature_vector(
    use_case: str,
    source_a_ping_ms: float,
    source_a_jitter_ms: float,
    source_a_loss_pct: float,
    source_b_ping_ms: float,
    source_b_jitter_ms: float,
    source_b_loss_pct: float,
    source_a_avg_1h: Optional[float] = None,
    source_a_avg_24h: Optional[float] = None,
    source_b_avg_1h: Optional[float] = None,
    source_b_avg_24h: Optional[float] = None,
    dt: Optional[datetime] = None,
) -> dict:
    """
    Bygg komplett feature-vektor for modellen.

    Kombinerer tidspunkt, kilde A-målinger, kilde B-målinger og use-case.
    Returnerer en dict som kan konverteres til pandas DataFrame for XGBoost.

    Bruk:
        features = build_feature_vector(
            use_case="gaming",
            source_a_ping_ms=36, source_a_jitter_ms=3.2, source_a_loss_pct=0.5,
            source_b_ping_ms=32, source_b_jitter_ms=1.8, source_b_loss_pct=0.0,
        )
    """
    time_feats = extract_time_features(dt)
    a_feats    = extract_measurement_features(
        source_a_ping_ms, source_a_jitter_ms, source_a_loss_pct,
        source_a_avg_1h, source_a_avg_24h,
    )
    b_feats    = extract_measurement_features(
        source_b_ping_ms, source_b_jitter_ms, source_b_loss_pct,
        source_b_avg_1h, source_b_avg_24h,
    )
    uc_feats   = extract_use_case_features(use_case)

    # Prefiks med source_a_ og source_b_
    vector = {}
    vector.update(time_feats)
    vector.update({f"source_a_{k}": v for k, v in a_feats.items()})
    vector.update({f"source_b_{k}": v for k, v in b_feats.items()})
    vector.update(uc_feats)

    # Sammenlignende features (diff mellom kildene)
    vector["ping_diff"]   = round(source_a_ping_ms - source_b_ping_ms, 2)
    vector["jitter_diff"] = round(source_a_jitter_ms - source_b_jitter_ms, 2)
    vector["loss_diff"]   = round(source_a_loss_pct - source_b_loss_pct, 2)

    return vector


# Kolonner i riktig rekkefølge (må matche treningsdata)
FEATURE_COLUMNS = [
    "hour_of_day", "day_of_week", "is_weekend", "is_evening", "is_night", "is_rush_hour",
    "hour_sin", "hour_cos", "day_sin", "day_cos",
    "source_a_ping_ms", "source_a_jitter_ms", "source_a_packet_loss_pct",
    "source_a_jitter_ratio", "source_a_has_loss",
    "source_a_avg_1h_ms", "source_a_avg_24h_ms",
    "source_a_drift_from_1h", "source_a_drift_from_24h",
    "source_b_ping_ms", "source_b_jitter_ms", "source_b_packet_loss_pct",
    "source_b_jitter_ratio", "source_b_has_loss",
    "source_b_avg_1h_ms", "source_b_avg_24h_ms",
    "source_b_drift_from_1h", "source_b_drift_from_24h",
    "use_case_gaming", "use_case_streaming", "use_case_work",
    "ping_diff", "jitter_diff", "loss_diff",
]
