from fastapi import APIRouter

router = APIRouter(tags=["sources"])


@router.get("/sources")
async def get_sources():
    """Returnerer tilgjengelige målepunkter / kilder."""
    return {
        "sources": [
            {
                "id": "local",
                "label": "Min egen PC",
                "emoji": "🏠",
                "description": "Test direkte fra din nettleser",
                "long_description": (
                    "Denne kilden kjører testen direkte fra din nettleser og din internettforbindelse. "
                    "Det er den mest nøyaktige målingen for deg personlig, fordi den viser nøyaktig "
                    "hva du opplever fra din router og din ISP."
                ),
                "available": True,
                "location": None,
            },
            {
                "id": "heimnett_cgnat",
                "label": "Heimnett CGNAT",
                "emoji": "🌐",
                "description": "Norsk ISP-test via CGNAT-node i Oslo",
                "long_description": (
                    "Heimnett er en norsk bredbåndsleverandør som bruker CGNAT (Carrier-Grade NAT). "
                    "Dette målepunktet sitter i Heimnett sitt nettverk i Oslo og simulerer opplevelsen "
                    "til en typisk norsk hjemmebruker. CGNAT betyr at mange kunder deler én ekstern IP-adresse."
                ),
                "available": True,
                "location": "Oslo, Norge",
            },
            {
                "id": "fastip",
                "label": "FastIP.no",
                "emoji": "⚡",
                "description": "Norsk ISP med direkte NIX-tilkobling",
                "long_description": (
                    "FastIP.no er en norsk ISP med direkte peering på NIX (Norsk Internett-Utveksling). "
                    "Målepunktet sitter i FastIP sitt nettverk i Oslo og representerer en moderne norsk "
                    "ISP med god infrastruktur og lav latens til europeiske servere."
                ),
                "available": True,
                "location": "Oslo, Norge",
            },
            {
                "id": "telia",
                "label": "Telia Node",
                "emoji": "🔀",
                "description": "Telia backbone-node i Stockholm",
                "long_description": (
                    "Telia Carrier er en av verdens største transit-leverandører. "
                    "Målepunktet sitter i Telia sitt backbone-nettverk i Stockholm. "
                    "Dette viser latens fra en tier-1 ISP med direkte fiber til DE-CIX, AMS-IX og andre IXP-er. "
                    "Merk: Denne kilden er for øyeblikket ikke tilgjengelig for testing."
                ),
                "available": False,
                "location": "Stockholm, Sverige",
            },
        ]
    }
