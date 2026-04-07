"""
predict.py – Prediksjonsmodul for Looking Glass AI Route Optimizer

Laster trent modell og gjør prediksjoner basert på feature-vektor.

Bruk:
    python predict.py --use_case gaming \\
                      --source_a_ping 36 --source_a_jitter 3.2 --source_a_loss 0.5 \\
                      --source_b_ping 32 --source_b_jitter 1.8 --source_b_loss 0.0

TODO: Koble denne til FastAPI-endepunktet i server/routers/ai.py
"""

import argparse
import pathlib
import sys

MODEL_PATH = pathlib.Path(__file__).parent / "models" / "route_optimizer.pkl"


def load_model():
    """Laster trent modell fra disk."""
    try:
        import joblib
        model = joblib.load(MODEL_PATH)
        return model
    except FileNotFoundError:
        print(f"❌ Modell ikke funnet: {MODEL_PATH}")
        print("   Kjør 'python ml/train.py' for å trene modellen først.")
        sys.exit(1)
    except ImportError:
        print("❌ joblib ikke installert. Kjør: pip install joblib scikit-learn")
        sys.exit(1)


def predict(
    use_case: str,
    source_a_ping_ms: float,
    source_a_jitter_ms: float,
    source_a_loss_pct: float,
    source_b_ping_ms: float,
    source_b_jitter_ms: float,
    source_b_loss_pct: float,
) -> dict:
    """
    Gjør prediksjon: hvilken kilde er best for gitt use_case?

    Returnerer dict med:
    - best_source: 'source_a' eller 'source_b'
    - confidence: 0.0–1.0
    - probabilities: dict med sannsynligheter for begge klasser
    """
    from features import build_feature_vector, FEATURE_COLUMNS
    import pandas as pd

    model = load_model()

    feature_dict = build_feature_vector(
        use_case=use_case,
        source_a_ping_ms=source_a_ping_ms,
        source_a_jitter_ms=source_a_jitter_ms,
        source_a_loss_pct=source_a_loss_pct,
        source_b_ping_ms=source_b_ping_ms,
        source_b_jitter_ms=source_b_jitter_ms,
        source_b_loss_pct=source_b_loss_pct,
    )

    # Bygg DataFrame med korrekt kolonnerekkefølge
    available_cols = [c for c in FEATURE_COLUMNS if c in feature_dict]
    X = pd.DataFrame([feature_dict])[available_cols]

    # TODO: Sjekk at kolonner matcher modellens forventede features
    pred = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = model.classes_
        proba_dict = dict(zip(classes, [round(float(p), 4) for p in proba]))
        confidence = float(max(proba))
    else:
        proba_dict = {pred: 1.0}
        confidence = 1.0

    return {
        "best_source":   pred,
        "confidence":    round(confidence, 4),
        "probabilities": proba_dict,
    }


def main():
    parser = argparse.ArgumentParser(description="Looking Glass AI – Rute-prediksjon")
    parser.add_argument("--use_case",         default="gaming",
                        choices=["gaming", "streaming", "work"])
    parser.add_argument("--source_a_ping",    type=float, required=True)
    parser.add_argument("--source_a_jitter",  type=float, required=True)
    parser.add_argument("--source_a_loss",    type=float, default=0.0)
    parser.add_argument("--source_b_ping",    type=float, required=True)
    parser.add_argument("--source_b_jitter",  type=float, required=True)
    parser.add_argument("--source_b_loss",    type=float, default=0.0)
    args = parser.parse_args()

    result = predict(
        use_case=args.use_case,
        source_a_ping_ms=args.source_a_ping,
        source_a_jitter_ms=args.source_a_jitter,
        source_a_loss_pct=args.source_a_loss,
        source_b_ping_ms=args.source_b_ping,
        source_b_jitter_ms=args.source_b_jitter,
        source_b_loss_pct=args.source_b_loss,
    )

    print("\n🧠 Prediksjon:")
    print(f"   Best kilde  : {result['best_source']}")
    print(f"   Konfidens   : {result['confidence'] * 100:.1f}%")
    print(f"   Sannsynligheter: {result['probabilities']}")


if __name__ == "__main__":
    main()
