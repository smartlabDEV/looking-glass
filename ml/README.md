# 🧠 AI Route Optimizer – PPO + ExaBGP Pipeline

Looking Glass bruker **Reinforcement Learning (PPO)** kombinert med **ExaBGP** for å
optimere BGP Traffic Engineering i sanntid for en ISP med ~10 000 kunder og Huawei NE8000
som BNG.

---

## 1. Arkitektur

```
SmokePing (RRD)     TimescaleDB (NetFlow)
      │                     │
      └──────────┬───────────┘
                 │
         features/extractor.py
                 │  (12-dim state vector)
                 ▼
          PPO-agent (SB3)
         ml/models/bgp_ppo_agent.zip
                 │  (action 0-3)
                 ▼
       exabgp/announcer.py
                 │  (stdout API)
                 ▼
            ExaBGP
                 │  (iBGP UPDATE)
                 ▼
        Huawei NE8000 BNG
          (LOCAL_PREF)
```

---

## 2. Hvorfor PPO (og ikke XGBoost eller CNN/GRU)?

| Tilnærming | Ulemper |
|------------|---------|
| XGBoost (klassifikasjon) | Statisk — lærer ikke av konsekvenser over tid |
| CNN/GRU (deep learning) | Over-komplisert for 12 features, trenger mye data |
| **PPO (RL)** | ✅ Lærer av faktiske kostnader, håndterer tidsserie naturlig, unngår flapping via instability penalty |

PPO fra `stable-baselines3` er akademisk korrekt, godt dokumentert, og fungerer utmerket
for diskrete action spaces med kontinuerlige observasjoner.

---

## 3. State space (12 variabler)

| # | Variabel | Enhet | Beskrivelse |
|---|----------|-------|-------------|
| 0 | `transit_cost_per_mbit` | kr/Mbit | Aktuell transit-kostnad |
| 1 | `nix_utilization_pct` | % | NIX-lenke utnyttelse |
| 2 | `telia_latency_ms` | ms | Latency via Telia transit |
| 3 | `nix_latency_ms` | ms | Latency via NIX peering |
| 4 | `total_traffic_gbps` | Gbps | Totalt trafikkvolum |
| 5 | `transit_traffic_gbps` | Gbps | Trafikk via transit |
| 6 | `nix_traffic_gbps` | Gbps | Trafikk via NIX |
| 7 | `hour_of_day` | 0–23 | Time på døgnet |
| 8 | `day_of_week` | 0–6 | Dag (0=mandag) |
| 9 | `telia_latency_delta` | ms/30min | Latency-trend (positiv = stigende) |
| 10 | `nix_packet_loss_pct` | % | Pakketap via NIX |
| 11 | `telia_packet_loss_pct` | % | Pakketap via Telia |

---

## 4. Action space (4 valg)

| Action | Navn | Beskrivelse |
|--------|------|-------------|
| `0` | **hold** | Ingen BGP-endring |
| `1` | **nix_prefer** | LOCAL_PREF 200 på NIX-peer → NE8000 foretrekker NIX |
| `2` | **telia_prefer** | LOCAL_PREF 200 på Telia → NE8000 foretrekker transit |
| `3` | **ecmp** | Begge får LOCAL_PREF 150 → NE8000 load-balancer (ECMP) |

---

## 5. Reward function

```python
reward = 0

# NIX er gratis — spar transit-kostnad
if action == NIX_PREFER:
    reward += transit_cost * transit_gbps * 0.3

# Bonus: NIX er også raskere
if action == NIX_PREFER and nix_latency < telia_latency:
    reward += 5.0

# Straff: bruk av dyr transit når NIX er bra
if action == TELIA_PREFER and nix_latency < telia_latency:
    reward -= 10.0

# Instabilitet = BGP flapping → stor straff
if action != last_action and action != HOLD:
    reward -= 2.0

# Aktiv latency-kostnad
reward -= current_latency * 0.1

# Stigende latency er et varseltegn
if latency_delta > 5:
    reward -= latency_delta * 0.5
```

---

## 6. Trene modellen

```bash
cd looking-glass

# Installer avhengigheter
pip install -r ml/requirements.txt

# Tren PPO-agent (~100k timesteps, ~5 min på CPU)
python ml/agent/train.py

# Modellen lagres til ml/models/bgp_ppo_agent.zip
```

---

## 7. Kjøre i produksjon

```bash
# Kjør agenten hvert 5. minutt (300 sek)
python ml/agent/predict.py --interval 300
```

Agenten:
1. Henter state fra TimescaleDB + SmokePing via `features/extractor.py`
2. Sender state til PPO-modellen
3. Får tilbake action (0–3)
4. Kaller `exabgp/announcer.py` som skriver BGP-kommandoer til ExaBGP via stdout

---

## 8. ExaBGP oppsett mot NE8000

ExaBGP kjøres som en separat Docker-container (se `docker-compose.yml`).

### Konfigurasjon (`ml/exabgp/exabgp.conf`)
Rediger følgende TODO-verdier:
- `neighbor 10.0.0.1` → NE8000 management IP
- `router-id 10.0.0.100` → ExaBGP-containerens IP
- `local-as 65000` / `peer-as 65000` → Ditt AS-nummer

### NE8000 VRP — iBGP konfig
```
bgp 65000
  peer-group EXABGP
    peer-as 65000
  peer 10.0.0.100 as-number 65000
    peer-group EXABGP
```

ExaBGP sender BGP UPDATE med `LOCAL_PREF` til NE8000.
NE8000 foretrekker ruten med **høyest LOCAL_PREF**.

---

## 9. TODO-liste for produksjon

- [ ] Fyll inn NE8000 IP og AS-nummer i `exabgp/exabgp.conf`
- [ ] Fyll inn `NIX_NEXT_HOP` og `TELIA_NEXT_HOP` i `exabgp/announcer.py`
- [ ] Hent topp-prefixer fra NetFlow og legg til i `MANAGED_PREFIXES`
- [ ] Koble `features/extractor.py` til TimescaleDB (pmacct/NetFlow)
- [ ] Koble `features/extractor.py` til SmokePing RRD
- [ ] Hent NIX-utnyttelse fra NE8000 via SNMP/Nornir
- [ ] Tren modellen på produksjonsdata (erstatt simulert `_get_obs()`)
- [ ] Sett opp re-trening ukentlig med nye data
- [ ] Legg til Prometheus-metrics for action-valg og reward
