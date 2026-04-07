"""
ExaBGP controller — mottaker og sender av BGP-meldinger.
Leser kommandoer fra stdin (ExaBGP API) og handler deretter.

ExaBGP kaller denne prosessen og kommuniserer via stdin/stdout.
"""

import json
import logging
import sys

from ml.exabgp.announcer import (
    hold,
    load_balance_ecmp,
    prefer_nix,
    prefer_telia,
)

logger = logging.getLogger(__name__)


def main():
    """Hovedloop — leser BGP-events fra ExaBGP"""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,  # ExaBGP leser stdout — logg til stderr
    )

    logger.info("🔌 ExaBGP controller startet")

    while True:
        try:
            line = sys.stdin.readline().strip()
            if not line:
                continue

            msg = json.loads(line)

            # BGP neighbor kom opp
            if msg.get("type") == "state" and msg.get("state") == "up":
                neighbor = msg["neighbor"]["address"]["peer"]
                logger.info(f"✅ BGP-nabo oppe: {neighbor}")

            # Mottatt BGP UPDATE
            elif msg.get("type") == "update":
                prefix = (
                    msg["neighbor"]["message"]["update"]
                    .get("announce", {})
                    .get("ipv4 unicast", {})
                )
                if prefix:
                    logger.info(f"📨 Mottatt prefix: {list(prefix.keys())}")

        except json.JSONDecodeError:
            pass
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
