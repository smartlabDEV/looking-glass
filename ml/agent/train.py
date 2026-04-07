"""
Tren PPO-agenten for BGP route optimization.

Bruk:
    python ml/agent/train.py

Modellen lagres i ml/models/bgp_ppo_agent.zip
"""

import os
import sys

# Legg til prosjektets rotmappe i Python-path slik at ml-pakken er tilgjengelig
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from ml.environment.bgp_env import BGPRoutingEnv


def train(total_timesteps: int = 100_000):
    env = make_vec_env(BGPRoutingEnv, n_envs=4)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,       # Fremtidsrabatt
        gae_lambda=0.95,
        clip_range=0.2,
        tensorboard_log="./ml/logs/",
    )

    model.learn(total_timesteps=total_timesteps)

    os.makedirs("ml/models", exist_ok=True)
    model.save("ml/models/bgp_ppo_agent")
    print("✅ Modell lagret: ml/models/bgp_ppo_agent.zip")


if __name__ == "__main__":
    train()
