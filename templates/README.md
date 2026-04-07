# templates/ — Jinja2-maler for Looking Glass

Denne mappen inneholder Jinja2-maler klare for pipeline/workflow-bruk.
Malene er **ikke koblet til koden ennå** — de legges her klare for når
du bygger hele automatiserings-pipelinen.

---

## 📁 Mappestruktur

```
templates/
├── README.md                          ← Denne filen
│
├── inventory/                         ← Nornir inventory
│   ├── hosts.j2                       ← Generer hosts.yml fra BECS-data
│   └── groups.j2                      ← Generer groups.yml
│
├── huawei/                            ← Huawei VRP (NE8000 M4 + 6730)
│   ├── bgp_peer.j2                    ← Legg til ny BGP peer
│   ├── bgp_community.j2               ← Sett BGP communities
│   ├── prefix_list.j2                 ← Prefix-liste
│   ├── route_policy.j2                ← Route-policy / route-map
│   └── traceroute_cmd.j2              ← Dynamisk traceroute-kommando
│
├── waystream/                         ← Waystream iBOS (PacketFront/BECS)
│   ├── service_l3.j2                  ← L3 service konfig
│   ├── vlan.j2                        ← VLAN konfig
│   └── traceroute_cmd.j2              ← Traceroute-kommando
│
├── becs/                              ← BECS/PacketFront API payloads
│   ├── service_create.j2              ← Opprett ny service
│   └── service_modify.j2              ← Endre eksisterende service
│
└── docker/                            ← Docker/infrastruktur
    ├── nornir_config.j2               ← Nornir config.yml
    └── smokeping_target.j2            ← SmokePing target-konfig
```

---

## 1. Hva er dette?

[Jinja2](https://jinja.palletsprojects.com/) er et Python-basert mal-system
som gjør det enkelt å generere konfig-filer, API-payloads og inventory fra
dynamiske data (f.eks. BECS-data).

Malene her dekker hele stacken:

| Mappe | Formål |
|---|---|
| `inventory/` | Generer Nornir `hosts.yml` og `groups.yml` fra BECS |
| `huawei/` | Huawei VRP-kommandoer (NE8000 M4, 6730) |
| `waystream/` | Waystream iBOS (tidl. PacketFront) konfig |
| `becs/` | BECS REST API JSON-payloads |
| `docker/` | Infrastruktur-konfig (Nornir, SmokePing) |

---

## 2. Hvordan bruke malene

### Grunnleggende Python-eksempel

```python
from jinja2 import Environment, FileSystemLoader
import json

# Sett opp Jinja2-miljø som peker på templates/-mappen
env = Environment(loader=FileSystemLoader('templates/'))

# Eksempel: Generer Nornir inventory fra BECS-data
template = env.get_template('inventory/hosts.j2')
becs_data = fetch_from_becs()  # din BECS-klient
rendered = template.render(devices=becs_data['devices'])

with open('inventory/hosts.yml', 'w') as f:
    f.write(rendered)
```

### Eksempel: Generer Huawei BGP-peer konfig

```python
template = env.get_template('huawei/bgp_peer.j2')
config = template.render(
    local_asn=65001,
    peer_ip='185.1.2.3',
    peer_asn=2116,
    peer_description='NIX-Steam-Valve',
    is_ix_peer=True,
    prefix_list_in='STEAM-IN',
    prefix_list_out='STEAM-OUT',
)
print(config)
```

### Eksempel: Generer BECS service-payload

```python
template = env.get_template('becs/service_create.j2')
payload = template.render(
    customer_id='CUST-1234',
    device_hostname='waystream-8024-oslo-1',
    interface='ge-0/0/1',
    vlan_id=100,
    speed_down=1000,
    speed_up=1000,
)

import httpx
resp = httpx.post(
    'https://becs.example.com/api/v1/services',
    content=payload,
    headers={'Content-Type': 'application/json'},
)
```

---

## 3. Koble til BECS (PacketFront/Waystream)

BECS eksponerer et REST API. Hent device-data og bruk direkte i malene:

```python
import httpx
from jinja2 import Environment, FileSystemLoader

BECS_URL = 'https://becs.example.com'
BECS_TOKEN = 'din-api-token'

def fetch_from_becs() -> dict:
    """Hent alle enheter fra BECS REST API"""
    resp = httpx.get(
        f'{BECS_URL}/api/v1/devices',
        headers={'Authorization': f'Bearer {BECS_TOKEN}'},
    )
    resp.raise_for_status()
    return resp.json()

env = Environment(loader=FileSystemLoader('templates/'))

# Generer hosts.yml
becs_data = fetch_from_becs()
template = env.get_template('inventory/hosts.j2')
rendered = template.render(devices=becs_data['devices'])

with open('inventory/hosts.yml', 'w') as f:
    f.write(rendered)

print("inventory/hosts.yml generert!")
```

---

## 4. Koble til Nornir

Når inventory er generert fra BECS, er Nornir klar:

```python
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command
from nornir.core.filter import F

# Initialiser Nornir med generert inventory
nr = InitNornir(config_file='inventory/nornir_config.yml')

# Kjør traceroute på alle Huawei-routere
huawei = nr.filter(F(data__vendor='huawei'))
result = huawei.run(
    task=netmiko_send_command,
    command_string='traceroute ip 8.8.8.8 source 10.0.0.1 ttl 1 15',
)

for host, task_result in result.items():
    print(f'{host}: {task_result[0].result}')
```

---

## 5. Komplett pipeline-eksempel

```
BECS REST API
     │
     ▼
fetch_from_becs()          ← Hent device-liste
     │
     ▼
hosts.j2 → hosts.yml       ← Render Nornir inventory
groups.j2 → groups.yml
     │
     ▼
InitNornir(hosts.yml)      ← Start Nornir
     │
     ▼
traceroute_cmd.j2          ← Bygg kommando per vendor
     │
     ▼
netmiko_send_command()     ← Kjør på router
     │
     ▼
parse_output()             ← Parser resultat
     │
     ▼
Looking Glass API          ← Returner til frontend
```

---

## 6. Variabel-referanse

### inventory/hosts.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `devices` | liste | Liste med device-objekter fra BECS |
| `device.hostname` | str | Unikt navn på enheten |
| `device.mgmt_ip` | str | Management IP-adresse |
| `device.platform` | str | `huawei` eller `waystream_ibos` |
| `device.vendor` | str | `huawei` eller `waystream` |
| `device.role` | str | `core`, `dist` eller `access` |
| `device.site` | str | Stedsnavn (f.eks. `oslo`) |
| `device.becs_id` | str | BECS intern device-ID |

### inventory/groups.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `huawei_username` | str | SSH-brukernavn for Huawei |
| `huawei_password` | str | SSH-passord for Huawei |
| `waystream_username` | str | SSH-brukernavn for Waystream |
| `waystream_password` | str | SSH-passord for Waystream |

### huawei/bgp_peer.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `local_asn` | int | Lokalt AS-nummer |
| `peer_ip` | str | IP til BGP-peer |
| `peer_asn` | int | AS-nummer til peer |
| `peer_description` | str | Beskrivelse av peer |
| `peer_password` | str | (valgfri) MD5-passord |
| `prefix_list_in` | str | (valgfri) route-policy for import |
| `prefix_list_out` | str | (valgfri) route-policy for eksport |
| `is_ix_peer` | bool | true = sett next-hop-local |

### huawei/bgp_community.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `policy_name` | str | Navn på route-policy |
| `node_id` | int | Node-nummer i sekvensen |
| `community_filter` | str | Community-filter å matche |
| `local_preference` | int | Local-preference verdi |
| `community_value` | str | Community som settes |

### huawei/prefix_list.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `list_name` | str | Navn på prefix-listen |
| `prefixes` | liste | Liste med prefix-objekter |
| `prefix.network` | str | Nettverksadresse |
| `prefix.mask` | str | Prefixlengde |
| `prefix.ge` | int | (valgfri) greater-equal |
| `prefix.le` | int | (valgfri) less-equal |

### huawei/route_policy.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `policy_name` | str | Navn på route-policy |
| `node_id` | int | Node-nummer i sekvensen |
| `match_prefix_list` | str | (valgfri) ip-prefix list |
| `match_as_path` | str | (valgfri) as-path-filter |
| `set_local_pref` | int | (valgfri) local-preference |
| `set_med` | int | (valgfri) MED/cost verdi |
| `set_community` | str | (valgfri) community-verdi |

### huawei/traceroute_cmd.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `target` | str | Destinasjons-IP eller hostname |
| `source_ip` | str | Kilde-IP på routeren |
| `vrf` | str | (valgfri) VRF-navn |
| `max_hops` | int | (valgfri) maks TTL, standard 15 |
| `verbose` | bool | (valgfri) verbose output, standard false |

### waystream/service_l3.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `interface` | str | Interface navn |
| `description` | str | Service-beskrivelse |
| `ip_address` | str | IP-adresse |
| `subnet_mask` | str | Nettmaske |
| `vlan_id` | int | (valgfri) VLAN-ID for dot1q |
| `vrf` | str | (valgfri) VRF-navn, standard `internet` |

### waystream/vlan.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `vlan_id` | int | VLAN-ID |
| `vlan_name` | str | VLAN-navn/beskrivelse |
| `interface` | str | (valgfri) interface å assosiere |
| `tagged` | bool | (valgfri) true = tagged, standard true |

### waystream/traceroute_cmd.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `target` | str | Destinasjons-IP eller hostname |
| `source_ip` | str | (valgfri) kilde-IP |

### becs/service_create.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `customer_id` | str | BECS kunde-ID |
| `service_type` | str | (valgfri) service-type, standard `l3_internet` |
| `device_hostname` | str | Hostname til Waystream i BECS |
| `interface` | str | Interface navn |
| `vlan_id` | int | VLAN-ID |
| `speed_down` | int | Nedlastingshastighet Mbit/s |
| `speed_up` | int | Opplastingshastighet Mbit/s |
| `vrf` | str | (valgfri) VRF, standard `internet` |
| `description` | str | (valgfri) beskrivelse |

### becs/service_modify.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `service_id` | str | BECS service-ID |
| `speed_down` | int | (valgfri) ny nedlastingshastighet Mbit/s |
| `speed_up` | int | (valgfri) ny opplastingshastighet Mbit/s |
| `description` | str | (valgfri) ny beskrivelse |
| `vrf` | str | (valgfri) VRF-navn |
| `enabled` | bool | (valgfri) aktiver/deaktiver service |

### docker/nornir_config.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `inventory_path` | str | Sti til inventory-mappe |
| `num_workers` | int | (valgfri) parallelle workers, standard 10 |
| `log_level` | str | (valgfri) loggnivå, standard `INFO` |

### docker/smokeping_target.j2

| Variabel | Type | Beskrivelse |
|---|---|---|
| `target_name` | str | Unikt target-navn (uten mellomrom) |
| `target_label` | str | Visningsnavn i SmokePing GUI |
| `target_location` | str | Stedsangivelse |
| `target_ip` | str | IP-adresse eller hostname |
| `alerts` | str | (valgfri) SmokePing-alerts |

---

## ⚠️ Viktige merknader

- **Malene er IKKE koblet til kode ennå** — de legges her klare for
  pipeline-bygging
- Alle Huawei-kommandoer bruker **VRP-syntax** (ikke Cisco IOS!)
- BECS-maler bruker **JSON-format** (REST API payload)
- Waystream-maler har **TODO-kommentarer** der syntax må verifiseres mot
  din spesifikke iBOS-versjon
- Passord og hemmeligheter skal **aldri** hardkodes i maler — bruk
  miljøvariabler eller vault

---

## 🔗 Lenker

- [Jinja2 dokumentasjon](https://jinja.palletsprojects.com/)
- [Nornir dokumentasjon](https://nornir.readthedocs.io/)
- [BECS / PacketFront](https://pfsw.com/becs/)
- [Waystream](https://www.waystream.com/)
- [Huawei VRP konfigurasjon](https://support.huawei.com/enterprise/en/doc/EDOC1100278197)
