# 🧠 AI Route Optimizer – ML Pipeline

Looking Glass bruker maskinlæring for å anbefale best internett-kilde for ulike brukstilfeller.

## Hva gjør modellen?

Modellen løser et binært klassifikasjonsproblem:
> «Gitt nåværende nettverksmålinger og tidspunkt – hvilken kilde (A eller B) vil gi lavest latens?»

## Features (inngangsverdier)

| Feature | Forklaring |
|---------|------------|
| `hour_of_day` | Time (0–23) |
| `day_of_week` | Dag (0=mandag, 6=søndag) |
| `is_weekend` | 1 hvis helg |
| `is_evening` | 1 hvis kl 18–23 |
| `is_night` | 1 hvis kl 0–6 |
| `source_a_ping_ms` | Øyeblikkelig ping fra kilde A |
| `source_b_ping_ms` | Øyeblikkelig ping fra kilde B |
| `source_a_jitter_ms` | Jitter fra kilde A |
| `source_b_jitter_ms` | Jitter fra kilde B |
| `source_a_loss_pct` | Pakketap fra kilde A |
| `source_b_loss_pct` | Pakketap fra kilde B |
| `source_a_avg_1h` | 1-times gjennomsnitt, kilde A |
| `source_b_avg_1h` | 1-times gjennomsnitt, kilde B |
| `use_case_gaming` | 1 hvis gaming |
| `use_case_streaming` | 1 hvis streaming |
| `use_case_work` | 1 hvis jobb |

## Kjente mønstre i dataen

- **Mandag 07–09**: Heimnett CGNAT er overbelastet pga. bedriftsstart → FastIP er best
- **Fredag 17–22**: Mange hjemme og streamer → FastIP er best pga. NIX-peering
- **Natt 00–05**: Lite trafikk → Heimnett CGNAT er best (laveste absolutte ping)
- **Helg**: Variabelt – avhenger av faktiske målinger

## Trene modellen

```bash
cd looking-glass

# Installer avhengigheter
pip install pandas scikit-learn xgboost joblib

# Tren
python ml/train.py
```

## Gjøre prediksjoner

```bash
python ml/predict.py \
  --use_case gaming \
  --source_a_ping 36 --source_a_jitter 3.2 --source_a_loss 0.5 \
  --source_b_ping 32 --source_b_jitter 1.8 --source_b_loss 0.0
```

Eksempel-output:
```
🧠 Prediksjon:
   Best kilde  : fastip
   Konfidens   : 87.3%
   Sannsynligheter: {'heimnett_cgnat': 0.127, 'fastip': 0.873}
```

## Produksjon: Koble til TimescaleDB

For produksjonsbruk bør du erstatte CSV-filen med faktiske målinger fra TimescaleDB:

```sql
-- Eksempel: Hent siste 7 dagers målinger
SELECT
    time_bucket('1 hour', measured_at) AS hour,
    source_id,
    target_id,
    AVG(ping_ms) AS avg_ping,
    STDDEV(ping_ms) AS jitter,
    SUM(packet_loss) / COUNT(*) * 100 AS loss_pct
FROM measurements
WHERE measured_at > NOW() - INTERVAL '7 days'
GROUP BY 1, 2, 3
ORDER BY 1;
```

## Modell-arkitektur

```
Rå målinger (TimescaleDB)
         ↓
  features.py (feature engineering)
         ↓
  XGBoost Classifier
         ↓
  best_source + confidence
         ↓
  FastAPI /api/recommend
         ↓
  Frontend AI-tab
```

## TODO

- [ ] Integrer TimescaleDB som datakilde
- [ ] Automatisk re-trening (cron job / Airflow)
- [ ] MLflow for eksperiment-tracking
- [ ] Hyperparameter-tuning med Optuna
- [ ] A/B testing av modellversjoner
- [ ] Legg til flere sources (Telia, Telenor)
