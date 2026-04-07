"""
BGP-annonsering via ExaBGP.
RL-agenten kaller disse funksjonene for å endre ruting på NE8000.

Metode: ExaBGP sender BGP UPDATE til NE8000.
NE8000 velger rute basert på LOCAL_PREF.
HIGH LOCAL_PREF = foretrekkes!
"""

import logging
import sys

logger = logging.getLogger(__name__)

# TODO: Fyll inn dine faktiske next-hops!
NIX_NEXT_HOP = "193.156.x.x"    # Din NIX-peer next-hop
TELIA_NEXT_HOP = "80.91.x.x"    # Din Telia-transit next-hop

# Prefixer vi styrer (topp-destinasjoner)
# Hentes ideelt fra NetFlow — hvilke prefixer bruker mest transit?
MANAGED_PREFIXES = [
    "208.64.200.0/24",   # Steam/Valve
    "45.55.32.0/19",     # Netflix
    "35.186.0.0/16",     # Google/YouTube
    "13.107.6.0/24",     # Microsoft Teams
    # TODO: Legg til dine topp-prefixer fra NetFlow!
]


def _announce(prefix: str, next_hop: str, local_pref: int):
    """Send BGP announcement via ExaBGP stdout API"""
    cmd = (
        f"announce route {prefix} "
        f"next-hop {next_hop} "
        f"local-preference {local_pref}\n"
    )
    sys.stdout.write(cmd)
    sys.stdout.flush()
    logger.info(f"📡 Annonsert: {prefix} via {next_hop} LP={local_pref}")


def _withdraw(prefix: str):
    """Trekk tilbake BGP-rute"""
    cmd = f"withdraw route {prefix}\n"
    sys.stdout.write(cmd)
    sys.stdout.flush()
    logger.info(f"🗑️  Trukket tilbake: {prefix}")


def prefer_nix():
    """
    Action 1: Foretrekk NIX-peering for alle managed prefixer.
    Setter LOCAL_PREF 200 på NIX (høyere = foretrekkes).
    NE8000 vil velge NIX over Telia (default LP 100).
    """
    logger.info("🔀 Action: PREFER NIX — setter LOCAL_PREF 200")
    for prefix in MANAGED_PREFIXES:
        _announce(prefix, NIX_NEXT_HOP, local_pref=200)


def prefer_telia():
    """
    Action 2: Foretrekk Telia transit.
    Brukes hvis NIX har problemer.
    """
    logger.info("🔀 Action: PREFER TELIA — setter LOCAL_PREF 200")
    for prefix in MANAGED_PREFIXES:
        _announce(prefix, TELIA_NEXT_HOP, local_pref=200)


def load_balance_ecmp():
    """
    Action 3: ECMP load-balance mellom NIX og Telia.
    Begge får LOCAL_PREF 150 — NE8000 load-balancer.
    """
    logger.info("⚖️  Action: ECMP — load-balance NIX + Telia")
    for prefix in MANAGED_PREFIXES:
        _announce(prefix, NIX_NEXT_HOP, local_pref=150)
        _announce(prefix, TELIA_NEXT_HOP, local_pref=150)


def hold():
    """Action 0: Ingen endring"""
    logger.info("✋ Action: HOLD — ingen BGP-endring")


def apply_action(action: int):
    """Kall riktig funksjon basert på RL-agent action"""
    actions = {
        0: hold,
        1: prefer_nix,
        2: prefer_telia,
        3: load_balance_ecmp,
    }
    actions.get(action, hold)()
