# 🔭 Looking Glass for vanlig folk

> Se nøyaktig hvilken vei dine datapakker tar fra deg til spillserveren, Netflix eller jobbverktøyet ditt – hopp for hopp.

---

## Hva er Looking Glass?

Et **Looking Glass** er et verktøy som nettverksingeniører bruker for å se rutene mellom servere på internett. Vi har tatt dette og gjort det tilgjengelig for alle – med norsk forklaring, emojier og en AI som anbefaler beste internett-kilde.

```
Du: Hei, kan du nå Valorant-serveren i London?

[Hjemmeruter] → [ISP-fiber] → [BNG Oslo] → [NIX] → [DE-CIX Frankfurt] → [Valorant EU]
    1 ms          3 ms          5 ms         7 ms        23 ms               42 ms
```

---

## Hurtigstart

```bash
# Med Docker (anbefalt)
docker-compose up

# Åpne nettleseren
open http://localhost:8000
```

### Uten Docker

```bash
cd server
pip install -r requirements.txt
uvicorn app:app --reload
```

---

## Skjermbilde (ASCII)

```
╔═══════════════════════════════════════════════════════════╗
║  🔭 Looking Glass for vanlig folk              🧠 AI-drevet ║
╠═══════════════════════════════════════════════════════════╣
║  📡 Test fra: [🏠 Min PC] [🌐 Heimnett] [⚡ FastIP]       ║
╠═══════════════════════════════════════════════════════════╣
║  [🔭 Nett-reise] [📊 Sammenlign] [🧠 AI Anbefaling]       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  🎮 Gaming                                                ║
║  [Steam 🇩🇪] [Valorant 🇬🇧] [CS2 🇸🇪] [LoL 🇳🇱]          ║
║                                                           ║
║  01 🏠 Hjemmeruter           ............ 1.2 ms  🟢     ║
║     │                                                     ║
║  02 🔌 ISP Fiber-node Oslo   ............ 3.4 ms  🟢     ║
║     │                                                     ║
║  03 🔀 NIX – Norsk IX        ............ 7.1 ms  🟢     ║
║     │                                                     ║
║  04 ⚡ DE-CIX Frankfurt      ............ 23.8 ms 🟢     ║
║     │                                                     ║
║  05 🔫 Valorant EU           ............ 42.1 ms 🟡     ║
╚═══════════════════════════════════════════════════════════╝
```

---

## API-endepunkter

### Hent alle servere
```bash
curl http://localhost:8000/api/servers
```

### Hent alle kilder
```bash
curl http://localhost:8000/api/sources
```

### Traceroute
```bash
curl "http://localhost:8000/api/traceroute?target=valorant&source=local"
curl "http://localhost:8000/api/traceroute?target=netflix&source=fastip"
```

### Ping til én server
```bash
curl "http://localhost:8000/api/ping/single?target=steam&source=local"
```

### Ping til alle servere
```bash
curl "http://localhost:8000/api/ping/multi?targets=steam,valorant,cs2&source=heimnett_cgnat"
```

### AI-anbefaling
```bash
curl "http://localhost:8000/api/recommend?use_case=gaming&source_a=heimnett_cgnat&source_b=fastip"
```

---

## Kilde-system

| Kilde | Beskrivelse | Tilgjengelighet |
|-------|-------------|-----------------|
| 🏠 Min egen PC | Direkte fra nettleseren din | Alltid |
| 🌐 Heimnett CGNAT | Norsk ISP med CGNAT, Oslo | ✅ Tilgjengelig |
| ⚡ FastIP.no | Norsk ISP med direkte NIX-peering | ✅ Tilgjengelig |
| 🔀 Telia Node | Telia backbone, Stockholm | ❌ Ikke tilgjengelig |

---

## AI-pipeline

```
TimescaleDB / mock CSV
        ↓
ml/features.py  (feature engineering)
        ↓
ml/train.py     (XGBoost trening)
        ↓
ml/models/route_optimizer.pkl
        ↓
server/models/route_optimizer.py  (regelbasert prototype)
        ↓
GET /api/recommend
```

Se [ml/README.md](ml/README.md) for full dokumentasjon av ML-pipelinen.

---

## Legge til nye servere

Rediger `server/data/servers.json`:

```json
{
  "id": "min-server",
  "label": "Min Server",
  "emoji": "🖥️",
  "location": "Oslo, Norge",
  "flag": "🇳🇴",
  "ip": "1.2.3.4",
  "description": "Beskrivelse av serveren",
  "why_it_matters": "Hvorfor dette er viktig for brukerne",
  "good_ping_ms": 10,
  "ok_ping_ms": 30,
  "category": "gaming"
}
```

Legg også til mock-målinger i `server/data/mock_measurements.json`.

---

## Legge til nytt målepunkt (kilde)

1. Legg til kilde i `server/routers/sources.py`
2. Legg til mock-målinger i `server/data/mock_measurements.json`
3. Legg til norske hopp-definisjoner i `server/routers/traceroute.py` under `NORWAY_HOPS`
4. Oppdater frontend source-tabs i `server/static/app.js`

For ekte målinger: Deploy en agent-node (se `DEVELOPERS.md`).

---

## Arkitektur

```
┌─────────────────────────────────────────────────┐
│                  Nettleser (SPA)                │
│   app.js  ←→  lookingglass.js  ←→  style.css   │
└────────────────────┬────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────┐
│              FastAPI (server/app.py)            │
│  /api/servers  /api/ping  /api/traceroute  /ai  │
├─────────────────────────────────────────────────┤
│  Mock-data: servers.json  mock_measurements.json │
│  ML-modell: route_optimizer.py                  │
└─────────────────────────────────────────────────┘
```

---

## Lisens

MIT – Bruk fritt, men husk: alle IP-adresser og målinger er fiktive/mock.
