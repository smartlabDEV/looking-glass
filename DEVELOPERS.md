# 🛠️ DEVELOPERS.md – Teknisk dokumentasjon

Teknisk guide for utviklere som vil bidra til eller utvide Looking Glass.

---

## 1. Komplett API-kontrakt

### `GET /api/servers`
Returnerer alle servere gruppert i kategorier.

```json
{
  "categories": [
    {
      "id": "gaming",
      "label": "Gaming",
      "emoji": "🎮",
      "description": "Test forsinkelse til dine favorittspill-servere",
      "servers": [
        {
          "id": "valorant",
          "label": "Valorant",
          "emoji": "🔫",
          "location": "London, Storbritannia",
          "flag": "🇬🇧",
          "ip": "185.50.104.53",
          "description": "Riot Games Valorant EU-server",
          "why_it_matters": "...",
          "good_ping_ms": 20,
          "ok_ping_ms": 45,
          "category": "gaming"
        }
      ]
    }
  ]
}
```

### `GET /api/sources`
```json
{
  "sources": [
    {
      "id": "local",
      "label": "Min egen PC",
      "emoji": "🏠",
      "description": "...",
      "long_description": "...",
      "available": true,
      "location": null
    }
  ]
}
```

### `GET /api/traceroute?target={id}&source={id}`
```json
{
  "target": "valorant",
  "source": "local",
  "total_ms": 42.1,
  "hops": [
    {
      "hop": 1,
      "ip": "192.168.x.x",
      "hostname": "router.local",
      "label": "Hjemmeruter",
      "description": "Din hjemmeruter",
      "long_description": "...",
      "emoji": "🏠",
      "city": "Hjemme",
      "country": "Norge",
      "flag": "🇳🇴",
      "ms": 1.2,
      "status": "good",
      "fun_fact": "..."
    }
  ]
}
```

### `GET /api/ping/single?target={id}&source={id}`
```json
{
  "source": "local",
  "result": {
    "server_id": "valorant",
    "ms": 42.1,
    "jitter_ms": 2.1,
    "packet_loss_pct": 0.0,
    "status": "good",
    "score": 78,
    "verdict": "Bra",
    "verdict_long": "..."
  }
}
```

### `GET /api/ping/multi?targets={csv}&source={id}`
```json
{
  "source": "local",
  "results": [...],
  "summary": {
    "gaming_score": 82,
    "streaming_score": 91,
    "work_score": 75,
    "overall_score": 83,
    "best_server": "cloudflare-dns",
    "worst_server": "teams"
  }
}
```

### `GET /api/recommend?use_case={case}&source_a={id}&source_b={id}`
```json
{
  "use_case": "gaming",
  "best_source": "fastip",
  "best_source_label": "FastIP.no",
  "confidence": 0.85,
  "predicted_ping_ms": 28.5,
  "reason": "Kveldspeering: FastIP har direkte NIX-rute",
  "reason_long": "...",
  "alternatives": [...],
  "model_info": {
    "algorithm": "XGBoost",
    "training_samples": 8640,
    "last_trained": "2024-11-01T03:00:00Z",
    "features_used": [...]
  }
}
```

---

## 2. Implementere ekte traceroute

Nåværende implementasjon bruker mock-data. For ekte traceroute:

```python
# server/routers/traceroute.py
# TODO: Erstatt mock med ekte implementasjon

import subprocess
import re

def real_traceroute(target_ip: str) -> list[dict]:
    """
    Kjør ekte traceroute via systemkall.
    Krever at agenten kjører med nettverkstilgang.
    """
    result = subprocess.run(
        ["traceroute", "-n", "-m", "15", target_ip],
        capture_output=True, text=True, timeout=30
    )
    hops = []
    for line in result.stdout.splitlines()[1:]:
        match = re.match(r'\s*(\d+)\s+([\d.*]+)\s+([\d.]+) ms', line)
        if match:
            hops.append({
                "hop": int(match.group(1)),
                "ip": match.group(2),
                "ms": float(match.group(3)),
            })
    return hops
```

Alternativt: Bruk `scapy` for python-native traceroute:
```bash
pip install scapy
```

---

## 3. Koble til ekstern agent

For å måle fra flere lokasjoner (Heimnett CGNAT, FastIP, etc.) trenger du agent-noder.

### Agent-arkitektur

```
┌──────────────────┐         HTTP/WS          ┌─────────────────┐
│  Agent-node      │  ←──────────────────────  │  Looking Glass  │
│  (Oslo / SE)     │                           │  FastAPI Server │
│                  │  →──────────────────────  │                 │
│  - scapy         │  {measurements}           │  /api/ping      │
│  - ping3         │                           │  /api/traceroute│
│  - requests      │                           │                 │
└──────────────────┘                           └─────────────────┘
```

### Minimal agent (Python)

```python
# agent/agent.py
import time, requests, subprocess

SERVER_URL = "https://your-looking-glass.example.com"
AGENT_ID   = "heimnett_cgnat_oslo"
TARGETS    = ["185.50.104.53", "146.66.155.1"]  # Valorant, CS2

def measure_ping(ip: str) -> dict:
    # TODO: Bruk ping3 eller scapy for mer nøyaktige målinger
    result = subprocess.run(
        ["ping", "-c", "10", "-W", "2", ip],
        capture_output=True, text=True
    )
    # Parse output...
    return {"ping_ms": 42.0, "jitter_ms": 2.1, "packet_loss_pct": 0.0}

while True:
    for target in TARGETS:
        measurement = measure_ping(target)
        requests.post(f"{SERVER_URL}/api/ingest", json={
            "agent_id": AGENT_ID,
            "target_ip": target,
            **measurement,
        })
    time.sleep(60)
```

---

## 4. Trene ML-modellen

```bash
# 1. Installer avhengigheter
pip install pandas scikit-learn xgboost joblib

# 2. Tren på eksempeldata
python ml/train.py

# 3. Test prediksjon
python ml/predict.py \
  --use_case gaming \
  --source_a_ping 36 --source_a_jitter 3.2 --source_a_loss 0.5 \
  --source_b_ping 32 --source_b_jitter 1.8 --source_b_loss 0.0

# 4. Koble til FastAPI (TODO)
# Rediger server/routers/ai.py og importer ml/predict.py
```

---

## 5. Legge til nye servere

1. Legg til server-objekt i `server/data/servers.json` under riktig kategori
2. Legg til mock-målinger for alle kilder i `server/data/mock_measurements.json`
3. Legg til destinasjons-hopp i `server/routers/traceroute.py:EUROPEAN_HOPS` hvis ny by
4. Restart serveren

---

## 6. TimescaleDB data-format

For produksjonsbruk anbefales TimescaleDB:

```sql
CREATE TABLE measurements (
    measured_at     TIMESTAMPTZ NOT NULL,
    agent_id        TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    target_ip       INET,
    ping_ms         FLOAT,
    jitter_ms       FLOAT,
    packet_loss_pct FLOAT,
    hop_count       INTEGER
);

SELECT create_hypertable('measurements', 'measured_at');
CREATE INDEX ON measurements (agent_id, target_id, measured_at DESC);
```

### Spørring for ML-features

```sql
SELECT
    time_bucket('1 hour', measured_at) AS hour_bucket,
    agent_id AS source_id,
    target_id,
    AVG(ping_ms)         AS avg_ping_ms,
    STDDEV(ping_ms)      AS jitter_ms,
    AVG(packet_loss_pct) AS avg_loss_pct
FROM measurements
WHERE measured_at > NOW() - INTERVAL '30 days'
  AND agent_id IN ('heimnett_cgnat', 'fastip')
GROUP BY 1, 2, 3
ORDER BY 1;
```

---

## 7. TODO for web-utviklere

- [ ] **Ekte ping fra nettleser**: Bruk `fetch` med `performance.now()` for å måle RTT til API-endepunkter
- [ ] **WebSocket**: Bytt polling med WebSocket for live traceroute-strøm
- [ ] **PWA**: Legg til `manifest.json` og service worker for offline-støtte
- [ ] **Deling**: Implementer `/share/{id}` endepunkt for å dele rapport-kort som URL
- [ ] **Historikk**: Lagre målinger i `localStorage` og vis trend-graf
- [ ] **Dark/light mode**: Legg til toggle for lyst tema

---

## 8. Prosjektstruktur

```
looking-glass/
├── server/
│   ├── app.py              # FastAPI app
│   ├── requirements.txt
│   ├── routers/
│   │   ├── traceroute.py   # GET /api/traceroute
│   │   ├── ping.py         # GET /api/ping/single|multi
│   │   ├── servers.py      # GET /api/servers
│   │   ├── sources.py      # GET /api/sources
│   │   └── ai.py           # GET /api/recommend
│   ├── models/
│   │   ├── route_optimizer.py  # Regelbasert AI (TODO: XGBoost)
│   │   └── schemas.py          # Pydantic-modeller
│   ├── data/
│   │   ├── servers.json        # Serverdefinisjoner
│   │   └── mock_measurements.json
│   └── static/
│       ├── index.html
│       ├── style.css
│       ├── app.js
│       └── lookingglass.js
└── ml/
    ├── train.py
    ├── predict.py
    ├── features.py
    └── data/sample_training_data.csv
```
