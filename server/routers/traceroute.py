"""
Traceroute-router – returnerer mock traceroute med realistisk norsk nettverkstopologi.

TODO: implement real traceroute – kjør scapy/nmap/paris-traceroute fra agent-node.
Erstatt MOCK_HOPS med ekte ICMP-TTL-probing mot target IP.
"""

import json
import pathlib
import random
from fastapi import APIRouter, Query

router = APIRouter(tags=["traceroute"])

_SERVERS_PATH = pathlib.Path(__file__).parent.parent / "data" / "servers.json"


def _load_servers() -> dict:
    with open(_SERVERS_PATH) as fh:
        return json.load(fh)


def _find_server(server_id: str) -> dict | None:
    data = _load_servers()
    for cat in data["categories"]:
        for srv in cat["servers"]:
            if srv["id"] == server_id:
                return srv
    return None


# Felles norske hopp (hjemme → ISP → NIX)
NORWAY_HOPS = {
    "local": [
        {
            "label": "Hjemmeruter",
            "ip": "192.168.x.x",
            "hostname": "router.local",
            "description": "Din hjemmeruter",
            "long_description": "Dette er din hjemmeruter – den første enheten i kjeden fra deg til internett. Produsert av din ISP eller kjøpt selv.",
            "emoji": "🏠",
            "city": "Hjemme",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 1,
            "fun_fact": "De fleste hjemmerutere i Norge er fra Telenor, Altibox eller Telia. De bruker DHCP og NAT for å dele én IP-adresse.",
        },
        {
            "label": "ISP Fiber-node",
            "ip": "10.x.x.x",
            "hostname": "fiber-bng-01.oslo.isp.no",
            "description": "ISP sitt Broadband Network Gateway",
            "long_description": "BNG-en (Broadband Network Gateway) er der ISPen avslutter din fiber-forbindelse og gir deg internettilgang. Her skjer autentisering via PPPoE eller IPoE.",
            "emoji": "🔌",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 3,
            "fun_fact": "BNG-er håndterer tusenvis av kundeforbindelser samtidig. Juniper MX og Nokia SR er vanlige BNG-plattformer i Norge.",
        },
        {
            "label": "ISP Core-ruter",
            "ip": "185.x.x.x",
            "hostname": "core-rtr-01.oslo.isp.no",
            "description": "ISP sitt kjernenett i Oslo",
            "long_description": "Kjerneruteren er hjerte av ISPens nettverk. Herfra rutes pakker videre til riktig destinasjon – enten lokalt i Norge via NIX, eller ut i verden via transit.",
            "emoji": "⚡",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 5,
            "fun_fact": "Norske ISP-kjernenett bruker typisk BGP (Border Gateway Protocol) for å annonsere IP-prefikser til andre nettverk.",
        },
        {
            "label": "NIX – Norsk Internett-Utveksling",
            "ip": "193.156.x.x",
            "hostname": "nix-sw-01.nix.no",
            "description": "Norsk Internett-Utveksling",
            "long_description": "NIX er der alle norske ISPer møtes og utveksler trafikk direkte – uten å gå via utlandet. Det er som et norsk torg for internett-trafikk. Lokalisert i Oslo.",
            "emoji": "🔀",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 7,
            "fun_fact": "NIX ble grunnlagt i 1993 og er en av de eldste internett-utvekslingspunktene i Europa. Over 60 norske nettverk er tilkoblet.",
        },
    ],
    "heimnett_cgnat": [
        {
            "label": "Heimnett CGNAT-ruter",
            "ip": "100.x.x.x",
            "hostname": "cgnat-pe-01.oslo.heimnett.no",
            "description": "Heimnett CGNAT – deler IP med mange kunder",
            "long_description": "CGNAT (Carrier-Grade NAT) betyr at du og hundrevis av andre kunder deler en ekstern IPv4-adresse. Dette kan gi høyere latens og problemer med noen tjenester.",
            "emoji": "🌐",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 8,
            "fun_fact": "CGNAT ble innført fordi IPv4-adresser er en begrenset ressurs. IPv6 løser dette – men mange tjenester støtter fremdeles bare IPv4.",
        },
        {
            "label": "Heimnett Core",
            "ip": "178.x.x.x",
            "hostname": "core-01.oslo.heimnett.no",
            "description": "Heimnett kjernenett",
            "long_description": "Heimnetts kjernenett i Oslo. Herfra rutes trafikken videre til NIX for norske destinasjoner, eller til transit-leverandører for internasjonale mål.",
            "emoji": "🏢",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 11,
            "fun_fact": "Heimnett, som mange norske ISPer, bruker fiber-nett som de leier av Telenors eller Altibox sitt aksessnett.",
        },
        {
            "label": "NIX – Norsk Internett-Utveksling",
            "ip": "193.156.x.x",
            "hostname": "nix-sw-02.nix.no",
            "description": "Norsk Internett-Utveksling",
            "long_description": "NIX er der alle norske ISPer møtes og utveksler trafikk direkte – uten å gå via utlandet.",
            "emoji": "🔀",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 13,
            "fun_fact": "NIX utveksler daglig hundrevis av Gbps norsk internett-trafikk. Det meste av NRK, VG og andre norske nettsteder leveres herfra.",
        },
    ],
    "fastip": [
        {
            "label": "FastIP Access",
            "ip": "185.x.x.x",
            "hostname": "access-01.oslo.fastip.no",
            "description": "FastIP aksess-node",
            "long_description": "FastIP.no sin aksess-node i Oslo. FastIP har investert i direktepeering på NIX for å gi kundene lav latens.",
            "emoji": "⚡",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 4,
            "fun_fact": "FastIP er en av Norges mer tekniske ISPer med fokus på lav latens og god peering-politikk.",
        },
        {
            "label": "NIX – Norsk Internett-Utveksling",
            "ip": "193.156.x.x",
            "hostname": "nix-sw-03.nix.no",
            "description": "Norsk Internett-Utveksling",
            "long_description": "NIX er der alle norske ISPer møtes og utveksler trafikk direkte.",
            "emoji": "🔀",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 7,
            "fun_fact": "FastIP har direktepeering med de fleste norske innholdsleverandører på NIX, noe som gir svært lav latens til norske tjenester.",
        },
    ],
    "telia": [
        {
            "label": "Telia Stockholm Core",
            "ip": "62.x.x.x",
            "hostname": "sto-core-01.telia.net",
            "description": "Telia Carrier backbone Stockholm",
            "long_description": "Telia Carrier er en av verdens største transit-leverandører med fiber over hele Europa og til USA. Kjernenettverket i Stockholm er et knutepunkt.",
            "emoji": "🔵",
            "city": "Stockholm",
            "country": "Sverige",
            "flag": "🇸🇪",
            "ms_base": 8,
            "fun_fact": "Telia Carrier (tidligere TeliaSonera) driver fiber i over 60 land og er en av de store tier-1 ISPene som binder internett sammen.",
        },
        {
            "label": "Telia Gothenburg",
            "ip": "213.x.x.x",
            "hostname": "got-core-01.telia.net",
            "description": "Telia backbone – Göteborg",
            "long_description": "Telia sitt backbone-knutepunkt i Göteborg. Viktig node på veien mot Europa.",
            "emoji": "📡",
            "city": "Göteborg",
            "country": "Sverige",
            "flag": "🇸🇪",
            "ms_base": 12,
            "fun_fact": "Göteborg er et viktig knutepunkt for undersjøiske kabler mellom Skandinavia og resten av Europa.",
        },
    ],
}

# Hopp mellom NIX/Sverige og ulike europeiske destinasjoner
EUROPEAN_HOPS = {
    "amsterdam": [
        {
            "label": "AMS-IX – Amsterdam Internet Exchange",
            "ip": "80.249.x.x",
            "hostname": "ams-ix-01.ams-ix.net",
            "description": "Verdens nest største internett-utvekslingspunkt",
            "long_description": "AMS-IX i Amsterdam er et av verdens største internett-utvekslingspunkter med over 1000 tilkoblede nettverk og flere terabit per sekund i trafikk.",
            "emoji": "🌐",
            "city": "Amsterdam",
            "country": "Nederland",
            "flag": "🇳🇱",
            "ms_base": 20,
            "fun_fact": "AMS-IX ble grunnlagt i 1994. På en travel dag håndterer AMS-IX over 8 Tbps trafikk.",
        },
        {
            "label": "NL-Transit",
            "ip": "194.x.x.x",
            "hostname": "nl-transit-01.ams.net",
            "description": "Nederlandsk transit-nett",
            "long_description": "Transit-nettverk i Nederland som videresender trafikk mot Amsterdam-baserte servere.",
            "emoji": "🔗",
            "city": "Amsterdam",
            "country": "Nederland",
            "flag": "🇳🇱",
            "ms_base": 22,
            "fun_fact": "Nederland har verdens høyeste internett-penetrasjon og er et av Europas viktigste data-hubber.",
        },
    ],
    "frankfurt": [
        {
            "label": "DE-CIX Frankfurt",
            "ip": "80.81.x.x",
            "hostname": "de-cix-01.de-cix.net",
            "description": "Verdens største internett-utvekslingspunkt",
            "long_description": "DE-CIX i Frankfurt er verdens største IXP med over 1000 tilkoblede nettverk og kapasitet til over 14 Tbps. Kjernen av europeisk internett.",
            "emoji": "⚡",
            "city": "Frankfurt",
            "country": "Tyskland",
            "flag": "🇩🇪",
            "ms_base": 23,
            "fun_fact": "DE-CIX ble grunnlagt i 1995 og håndterer daglig mer trafikk enn alle norske ISPer til sammen. Frankfurt er Europas datahovedstad.",
        },
        {
            "label": "DE-Transit",
            "ip": "217.x.x.x",
            "hostname": "de-transit-02.fra.net",
            "description": "Tysk transit til destinasjon",
            "long_description": "Siste transit-hopp i Tyskland før pakken når destinasjonsserveren.",
            "emoji": "🔗",
            "city": "Frankfurt",
            "country": "Tyskland",
            "flag": "🇩🇪",
            "ms_base": 25,
            "fun_fact": "Frankfurt er hjemsted for over 50 datasentre og er Europas viktigste fiber-knutepunkt.",
        },
    ],
    "london": [
        {
            "label": "LINX – London Internet Exchange",
            "ip": "195.66.x.x",
            "hostname": "linx-01.linx.net",
            "description": "London Internet Exchange",
            "long_description": "LINX er Storbritannias største IXP og en av de viktigste i Europa. Lokalisert i London med over 800 tilkoblede nettverk.",
            "emoji": "🇬🇧",
            "city": "London",
            "country": "Storbritannia",
            "flag": "🇬🇧",
            "ms_base": 26,
            "fun_fact": "LINX håndterer over 5 Tbps trafikk daglig. Brexit har ikke påvirket Storbritannias rolle som internett-hub.",
        },
        {
            "label": "UK-Transit",
            "ip": "212.x.x.x",
            "hostname": "uk-transit-01.lon.net",
            "description": "Britisk transit-nett",
            "long_description": "Transit-nettverk i Storbritannia for videreformidling mot London-baserte servere.",
            "emoji": "🔗",
            "city": "London",
            "country": "Storbritannia",
            "flag": "🇬🇧",
            "ms_base": 28,
            "fun_fact": "London er et av verdens viktigste finanssentre, noe som driver enormt behov for lav-latens internett-infrastruktur.",
        },
    ],
    "dublin": [
        {
            "label": "INEX – Internet Neutral Exchange",
            "ip": "185.x.x.x",
            "hostname": "inex-01.inex.ie",
            "description": "Irsk internett-utvekslingspunkt",
            "long_description": "INEX er Irlands internett-utvekslingspunkt. Dublin er et viktig europeisk datasenter-knutepunkt, spesielt for amerikanske tech-giganter.",
            "emoji": "🇮🇪",
            "city": "Dublin",
            "country": "Irland",
            "flag": "🇮🇪",
            "ms_base": 32,
            "fun_fact": "Dublin huser europeiske hovedkontor for Google, Facebook, Twitter og mange andre tech-selskaper pga. gunstig skattepolitikk.",
        },
        {
            "label": "IE-Transit",
            "ip": "193.x.x.x",
            "hostname": "ie-transit-01.dub.net",
            "description": "Irsk transit til destinasjon",
            "long_description": "Siste transit-hopp i Irland mot destinasjonsserveren.",
            "emoji": "🔗",
            "city": "Dublin",
            "country": "Irland",
            "flag": "🇮🇪",
            "ms_base": 35,
            "fun_fact": "Irland tiltrekker tech-giganter med en selskapsskatt på 12.5% – lavest i Europa.",
        },
    ],
    "oslo": [
        {
            "label": "Lokal Oslo-ruter",
            "ip": "158.x.x.x",
            "hostname": "oslo-cdn-01.no",
            "description": "Oslo lokalt CDN-knutepunkt",
            "long_description": "Mange norske innholdsleverandører cacher innholdet sitt lokalt i Oslo for å gi norske brukere lav latens.",
            "emoji": "🇳🇴",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 8,
            "fun_fact": "Oslo er Norges internett-hub. Nesten all norsk internett-trafikk passerer gjennom Oslo-området.",
        },
    ],
    "stockholm": [
        {
            "label": "STHIX – Stockholm Internet Exchange",
            "ip": "194.68.x.x",
            "hostname": "sthix-01.sthix.net",
            "description": "Stockholms Internett-Utvekslingspunkt",
            "long_description": "STHIX i Stockholm er Skandinavias viktigste internett-utvekslingspunkt etter NIX. Godt koblet til DE-CIX og AMS-IX.",
            "emoji": "🇸🇪",
            "city": "Stockholm",
            "country": "Sverige",
            "flag": "🇸🇪",
            "ms_base": 10,
            "fun_fact": "Stockholm er hjemsted for Spotify, King, Mojang og mange andre tech-selskaper. Det reflekteres i god internett-infrastruktur.",
        },
    ],
    "anycast": [
        {
            "label": "Anycast-node Oslo",
            "ip": "unknown",
            "hostname": "anycast.local",
            "description": "Nærmeste anycast-instans",
            "long_description": "Anycast-adresser rutes automatisk til nærmeste node. Fra Norge vil dette typisk være en node i Oslo eller København.",
            "emoji": "🌍",
            "city": "Oslo",
            "country": "Norge",
            "flag": "🇳🇴",
            "ms_base": 5,
            "fun_fact": "Anycast er magisk – den samme IP-adressen finnes på tusenvis av steder verden over. BGP sørger for at du alltid når nærmeste node.",
        },
    ],
}

LOCATION_MAP = {
    "Frankfurt, Tyskland":    "frankfurt",
    "London, Storbritannia":  "london",
    "Amsterdam, Nederland":   "amsterdam",
    "Dublin, Irland":         "dublin",
    "Oslo, Norge":            "oslo",
    "Stockholm, Sverige":     "stockholm",
    "Anycast (global)":       "anycast",
}


def _hop_status(ms: float) -> str:
    if ms < 20:
        return "good"
    if ms < 50:
        return "good"
    if ms < 80:
        return "warn"
    return "slow"


def _build_traceroute(source: str, server: dict) -> list:
    location = server.get("location", "Frankfurt, Tyskland")
    dest_key = LOCATION_MAP.get(location, "frankfurt")

    base_hops_def = NORWAY_HOPS.get(source, NORWAY_HOPS["local"])
    eu_hops_def   = EUROPEAN_HOPS.get(dest_key, EUROPEAN_HOPS["frankfurt"])

    all_defs = base_hops_def + eu_hops_def

    hops = []
    for i, hd in enumerate(all_defs, start=1):
        ms = round(hd["ms_base"] + random.uniform(-0.8, 1.5), 1)
        hops.append({
            "hop": i,
            "ip": hd["ip"],
            "hostname": hd["hostname"],
            "label": hd["label"],
            "description": hd["description"],
            "long_description": hd["long_description"],
            "emoji": hd["emoji"],
            "city": hd["city"],
            "country": hd["country"],
            "flag": hd["flag"],
            "ms": ms,
            "status": _hop_status(ms),
            "fun_fact": hd["fun_fact"],
        })

    # Siste hopp – destinasjonsserveren
    from_ms = all_defs[-1]["ms_base"] if all_defs else 20
    final_ms = round(from_ms + random.uniform(0.5, 3.0), 1)
    hops.append({
        "hop": len(hops) + 1,
        "ip": server["ip"],
        "hostname": f"{server['id']}.{location.split(',')[0].lower().replace(' ', '')}.server",
        "label": server["label"],
        "description": server["description"],
        "long_description": server["why_it_matters"],
        "emoji": server["emoji"],
        "city": location.split(",")[0].strip(),
        "country": location.split(",")[1].strip() if "," in location else location,
        "flag": server["flag"],
        "ms": final_ms,
        "status": _hop_status(final_ms),
        "fun_fact": f"{server['label']} betjener millioner av brukere daglig. {server['why_it_matters']}",
    })

    return hops


@router.get("/traceroute")
async def get_traceroute(
    target: str = Query(..., description="Server-ID"),
    source: str = Query("local", description="Kilde-ID"),
):
    """
    TODO: implement real traceroute – bruk scapy eller paris-traceroute fra agent-node.
    Erstatt denne mock-implementasjonen med ekte ICMP TTL-probing.
    """
    server = _find_server(target)
    if server is None:
        return {"error": f"Server '{target}' ikke funnet", "hops": []}

    hops = _build_traceroute(source, server)
    total_ms = hops[-1]["ms"] if hops else 0.0

    return {
        "target": target,
        "source": source,
        "total_ms": total_ms,
        "hops": hops,
    }
