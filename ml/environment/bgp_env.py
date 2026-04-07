import gymnasium as gym
import numpy as np


class BGPRoutingEnv(gym.Env):
    """
    BGP Traffic Engineering miljø for Heimnett-størrelse ISP
    ~10 000 kunder, Huawei NE8000 BNG, NIX + Telia transit

    State space:
    - transit_cost_per_mbit    (kr/Mbit akkurat nå)
    - nix_utilization_pct      (0-100)
    - telia_latency_ms         (ms)
    - nix_latency_ms           (ms)
    - total_traffic_gbps       (nåværende volum)
    - transit_traffic_gbps     (hvor mye går via transit)
    - nix_traffic_gbps         (hvor mye går via NIX)
    - hour_of_day              (0-23)
    - day_of_week              (0-6)
    - telia_latency_delta      (endring siste 30min, positiv = stigende)
    - nix_packet_loss_pct      (0-100)
    - telia_packet_loss_pct    (0-100)

    Action space (discrete):
    0 = hold nåværende ruter (ingen endring)
    1 = flytt topp-prefix til NIX (LOCAL_PREF 200 på NIX-peer)
    2 = flytt topp-prefix til Telia transit
    3 = load-balance ECMP (begge)

    Reward:
    - transit_kostnad: negativt (vil minimere)
    - latency_penalty: negativt hvis latency øker
    - nix_bonus: positivt for NIX-bruk (gratis peering)
    - instability_penalty: negativt for hyppige endringer (unngå flapping!)
    """

    def __init__(self):
        super().__init__()

        # 12 state-variabler — øvre grenser per variabel:
        # [transit_cost, nix_util, telia_lat, nix_lat,
        #  total_gbps, transit_gbps, nix_gbps,
        #  hour, weekday, lat_delta, nix_loss, telia_loss]
        self.observation_space = gym.spaces.Box(
            low=np.zeros(12),
            high=np.array([
                100,   # transit_cost_per_mbit (kr/Mbit)
                100,   # nix_utilization_pct   (%)
                500,   # telia_latency_ms       (ms)
                500,   # nix_latency_ms         (ms)
                100,   # total_traffic_gbps     (Gbps)
                100,   # transit_traffic_gbps   (Gbps)
                100,   # nix_traffic_gbps       (Gbps)
                23,    # hour_of_day            (0-23)
                6,     # day_of_week            (0-6)
                50,    # telia_latency_delta    (ms/30min)
                100,   # nix_packet_loss_pct    (%)
                100,   # telia_packet_loss_pct  (%)
            ]),
            dtype=np.float32,
        )

        # 4 mulige actions
        self.action_space = gym.spaces.Discrete(4)

        self.last_action = 0
        self.steps = 0

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.last_action = 0
        self.steps = 0
        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        # Beregn reward basert på action og nåværende state
        state = self._get_obs()
        reward = self._compute_reward(action, state)

        self.last_action = action
        self.steps += 1

        obs = self._get_obs()
        done = False  # Kontinuerlig miljø

        return obs, reward, done, False, {}

    def _compute_reward(self, action, state):
        transit_cost = state[0]
        nix_util = state[1]
        telia_latency = state[2]
        nix_latency = state[3]
        transit_gbps = state[5]
        latency_delta = state[9]

        reward = 0.0

        # Spar penger på transit
        if action == 1:  # Flytt til NIX
            reward += transit_cost * transit_gbps * 0.3  # spar 30% transit
            if nix_latency < telia_latency:
                reward += 5.0  # bonus: NIX er også raskere!

        # Straff for å gå til transit når NIX er bra
        if action == 2 and nix_latency < telia_latency:
            reward -= 10.0

        # Straff for instabilitet (flapping!)
        if action != self.last_action and action != 0:
            reward -= 2.0

        # Straff for høy latency uansett
        reward -= (telia_latency if action == 2 else nix_latency) * 0.1

        # Straff for stigende latency (problem kommer!)
        if latency_delta > 5:
            reward -= latency_delta * 0.5

        return float(reward)

    def _get_obs(self):
        # TODO: I produksjon — hent fra TimescaleDB/SmokePing
        # For trening — returner simulert state
        return np.array(
            [
                np.random.uniform(5, 50),       # transit_cost_per_mbit
                np.random.uniform(10, 90),      # nix_utilization_pct
                np.random.uniform(8, 45),       # telia_latency_ms
                np.random.uniform(3, 12),       # nix_latency_ms
                np.random.uniform(1, 8),        # total_traffic_gbps
                np.random.uniform(0.5, 5),      # transit_traffic_gbps
                np.random.uniform(0.5, 3),      # nix_traffic_gbps
                float(np.random.randint(0, 24)),  # hour_of_day
                float(np.random.randint(0, 7)),   # day_of_week
                np.random.uniform(-10, 20),     # telia_latency_delta
                np.random.uniform(0, 2),        # nix_packet_loss_pct
                np.random.uniform(0, 5),        # telia_packet_loss_pct
            ],
            dtype=np.float32,
        )
