"""
Kjør PPO-agenten i produksjon.
Leser state fra TimescaleDB → beslutter action → sender til ExaBGP controller.

Kjøres kontinuerlig (hvert 5. minutt):
    python ml/agent/predict.py --interval 300
"""

import asyncio
import argparse
import logging
import os
import sys

# Legg til prosjektets rotmappe i Python-path slik at ml-pakken er tilgjengelig
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from stable_baselines3 import PPO

from ml.features.extractor import get_current_state
from ml.exabgp.announcer import apply_action

logger = logging.getLogger(__name__)

ACTIONS = {
    0: "hold       — ingen BGP-endring",
    1: "nix_prefer — LOCAL_PREF 200 på NIX-peer",
    2: "telia_prefer — LOCAL_PREF 200 på Telia-transit",
    3: "ecmp       — load-balance begge",
}


def run(interval: int = 300):
    model_path = "ml/models/bgp_ppo_agent"
    try:
        model = PPO.load(model_path)
    except FileNotFoundError:
        logger.error(
            f"❌ Modell ikke funnet: {model_path}.zip\n"
            "   Tren modellen først: python ml/agent/train.py"
        )
        sys.exit(1)
    logger.info("✅ PPO-modell lastet")

    while True:
        import time

        # Hent nåværende nettverkstilstand (kjør async funksjon synkront)
        state = asyncio.run(get_current_state())

        # RL-agent bestemmer action
        action, _ = model.predict(state, deterministic=True)

        logger.info(f"🧠 Action: {ACTIONS[int(action)]}")
        logger.info(
            f"   Transit: {state[0]:.1f} kr/Mbit | "
            f"NIX: {state[3]:.1f}ms | "
            f"Telia: {state[2]:.1f}ms"
        )

        # Utfør BGP-endring via ExaBGP
        apply_action(int(action))

        time.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    parser = argparse.ArgumentParser(description="PPO BGP Route Optimizer")
    parser.add_argument("--interval", type=int, default=300,
                        help="Sekunder mellom hver beslutning (standard: 300)")
    args = parser.parse_args()
    run(args.interval)
