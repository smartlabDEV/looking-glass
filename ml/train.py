"""
train.py – Treningsskript for Looking Glass AI Route Optimizer

Dette skriptet:
1. Laster treningsdata fra ml/data/sample_training_data.csv
2. Trekker ut features via features.py
3. Trener en XGBoost-modell (med RandomForest som fallback)
4. Evaluerer modellen og skriver ut metrics
5. Lagrer modellen til ml/models/route_optimizer.pkl

Kjør:
    python ml/train.py

TODO for produksjon:
- Hent data fra TimescaleDB istedenfor CSV
- Legg til kryss-validering
- Eksperiment-tracking med MLflow
- Automatisk re-trening hver uke
"""

import pathlib
import sys

import pandas as pd

DATA_PATH  = pathlib.Path(__file__).parent / "data" / "sample_training_data.csv"
MODEL_DIR  = pathlib.Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "route_optimizer.pkl"


def load_data() -> pd.DataFrame:
    """Laster treningsdata fra CSV."""
    print(f"📂 Laster data fra {DATA_PATH}…")
    df = pd.read_csv(DATA_PATH)
    print(f"   {len(df)} rader lastet")
    return df


def prepare_features(df: pd.DataFrame):
    """
    Forbereder features og labels.

    Features:
    - Tidspunkt (hour_of_day, day_of_week, is_weekend, is_evening)
    - Kilde A målinger (ping, jitter, pakketap, historisk snitt)
    - Kilde B målinger
    - Use-case one-hot

    Label:
    - best_source: 'heimnett_cgnat' eller 'fastip' (binær klassifikasjon)
    """
    # Feature-kolonner
    feature_cols = [
        "hour_of_day", "day_of_week", "is_weekend", "is_evening",
        "source_a_ping_ms", "source_b_ping_ms",
        "source_a_jitter_ms", "source_b_jitter_ms",
        "source_a_loss_pct", "source_b_loss_pct",
        "source_a_avg_1h", "source_b_avg_1h",
        "source_a_avg_24h", "source_b_avg_24h",
        "use_case_gaming", "use_case_streaming", "use_case_work",
    ]

    # One-hot encode use_case
    df["use_case_gaming"]    = (df["use_case"] == "gaming").astype(int)
    df["use_case_streaming"] = (df["use_case"] == "streaming").astype(int)
    df["use_case_work"]      = (df["use_case"] == "work").astype(int)

    # Legg til diff-features
    df["ping_diff"]   = df["source_a_ping_ms"] - df["source_b_ping_ms"]
    df["jitter_diff"] = df["source_a_jitter_ms"] - df["source_b_jitter_ms"]
    feature_cols += ["ping_diff", "jitter_diff"]

    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols]
    y = df["best_source"]

    return X, y, available_cols


def train_model(X, y):
    """
    Trener modellen.

    Prøver XGBoost først – faller tilbake til RandomForest hvis ikke installert.
    TODO: Legg til hyperparameter-tuning med Optuna.
    """
    try:
        from xgboost import XGBClassifier

        # Konverter labels til numerisk for XGBoost
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        model.fit(X, y_enc)
        # Wrapper for å få riktige class-labels
        model.classes_ = le.classes_

        original_predict      = model.predict
        original_predict_proba = model.predict_proba

        def predict_with_labels(X_in):
            return le.inverse_transform(original_predict(X_in))

        def predict_proba_wrapper(X_in):
            return original_predict_proba(X_in)

        model.predict       = predict_with_labels
        model.predict_proba = predict_proba_wrapper
        model._label_encoder = le

        print("✅ Bruker XGBoost")
        return model

    except ImportError:
        print("⚠️  XGBoost ikke funnet – bruker RandomForest som fallback")
        print("   Installer med: pip install xgboost")
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X, y)
        return model


def evaluate_model(model, X, y):
    """Evaluerer modellen og skriver ut metrics."""
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import accuracy_score, classification_report

    y_pred = model.predict(X)
    acc    = accuracy_score(y, y_pred)

    print("\n📊 Modell-evaluering:")
    print(f"   Treningsdata-nøyaktighet: {acc * 100:.1f}%")
    print("\n   Klassifikasjonsrapport:")
    print(classification_report(y, y_pred, zero_division=0))

    # TODO: Legg til kryss-validering for å unngå overfitting
    # cv_scores = cross_val_score(model, X, y, cv=5)
    # print(f"   Kryss-validering (5-fold): {cv_scores.mean()*100:.1f}% ± {cv_scores.std()*100:.1f}%")


def save_model(model):
    """Lagrer modell til disk."""
    import joblib
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Modell lagret: {MODEL_PATH}")


def main():
    print("🧠 Looking Glass – Route Optimizer Trening")
    print("=" * 50)

    try:
        import joblib
    except ImportError:
        print("❌ joblib ikke installert. Kjør: pip install joblib scikit-learn pandas")
        sys.exit(1)

    df = load_data()
    X, y, feature_cols = prepare_features(df)

    print(f"\n🔧 Features ({len(feature_cols)}):")
    for col in feature_cols:
        print(f"   - {col}")

    print(f"\n🏷️  Klasser: {y.unique().tolist()}")
    print(f"   Fordeling:\n{y.value_counts().to_string()}")

    model = train_model(X, y)
    evaluate_model(model, X, y)
    save_model(model)

    print("\n✨ Ferdig! Bruk predict.py for å gjøre prediksjoner.")


if __name__ == "__main__":
    main()
