# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenL2M (Open Layer 2 Management) is a Django 5.2 web application for managing network devices (switches, routers) via a unified web UI and REST API. It supports various vendors through pluggable device drivers (SNMP, SSH/Netmiko, REST APIs, vendor-specific APIs).

## Development Setup

```bash
cd /opt/openl2m
source venv/bin/activate
cd openl2m

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver 127.0.0.1:8000

# Create superuser
python manage.py createsuperuser
```

**Required**: `openl2m/openl2m/configuration.py` must exist (copy from `configuration.example.py`) with `SECRET_KEY`, `DATABASE`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` set.

## Commands

```bash
# Linting / formatting (run from repo root with venv active)
black openl2m/
flake8 openl2m/
pylint openl2m/
ruff check openl2m/
mypy openl2m/

# Tests
python manage.py test                          # all tests
python manage.py test switches.tests           # specific module
python manage.py test switches.tests.ClassName # specific class

# Build docs
cd docs && make html
```

Code style: max line length 120, Black formatting with `skip-string-normalization = true`.

## Coding Conventions
- **Style:** Follow PEP 8 strictly.
- **Naming:** `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Formatting:** Use 4 spaces for indentation. Max line length is 120 characters.
- **Types:** Use type hints for all function signatures.
- **Docstrings:** Required for all public modules, classes, and functions using the Google style format.

## Architecture

### Django Apps

- **`switches/`** — Core app: device management, VLAN/interface operations, logging, REST API
- **`users/`** — Authentication, user profiles, group-based access control, REST API
- **`notices/`** — System notifications
- **`counters/`** — Usage statistics/metrics
- **`openl2m/`** — Django project settings, URL routing, API root

### Request Flow

```
HTTP Request → urls.py → views.py (or api/ views)
                              ↓
                        actions.py
                              ↓
                  connect/connect.py   ← factory that selects the right driver
                              ↓
                  connect/connector.py ← base Connector class
                              ↓
                  vendor-specific connector (e.g. connect/snmp/, connect/aruba_aoscx/)
                              ↓
                        Network Device
```

### Device Driver System (`switches/connect/`)

`connect/connect.py` is the factory function that inspects the `Switch.connector_type` and instantiates the correct driver class. All drivers inherit from `Connector` (in `connect/connector.py`), which defines the interface expected by views/actions.

Driver directories:
- `snmp/` — Base SNMP driver plus vendor subclasses: `cisco/`, `comware/`, `juniper/`, `procurve/`, `arista_eos/`, `aruba_cx/`, `netgear/`, `mikrotik/`, `dell/`
- `aruba_aoscx/` — Aruba AOS-CX REST API
- `aruba_aoss_rest/` — Aruba AOS-S REST API
- `arista_eapi/` — Arista eAPI
- `junos_pyez/` — Juniper PyEZ
- `hpe_cw_rest/` — HPE Comware REST
- `hpe_cw7_nc/` — HPE Comware 7 NetConf (bundled `pyhpecw7` library)
- `commands_only/` — SSH-only (Netmiko)
- `napalm/` — Read-only Napalm driver
- `dummy/` — Demo/testing driver

`connect/classes.py` defines data classes shared across all drivers: `Interface`, `Vlan`, `EthernetAddress`, `NeighborDevice`, `PoePort`, `PoePSE`, etc.

### Key Files

| File | Purpose |
|------|---------|
| `switches/models.py` | `Switch`, `SwitchGroup`, `SnmpProfile`, `Command`, `Log`, `VLAN` models |
| `switches/constants.py` | `CONNECTOR_TYPE_*` constants and other app-wide constants |
| `switches/views.py` | Web UI view functions |
| `switches/actions.py` | Business logic called by both views and API |
| `switches/connect/connect.py` | Driver factory — maps connector type to class |
| `switches/connect/connector.py` | Base `Connector` class all drivers extend |
| `switches/connect/classes.py` | Shared data model classes (Interface, Vlan, etc.) |
| `switches/connect/constants.py` | Driver-level constants (SNMP OIDs, interface types, etc.) |
| `openl2m/settings.py` | Django settings (imports `configuration.py`) |
| `openl2m/urls.py` | Top-level URL routing |

### REST API

Built with Django REST Framework + drf-spectacular (OpenAPI). API views live in `switches/api/` and `users/api/`. Schema available at `/api/swagger-ui/`.

### Authentication

Standard Django auth plus optional LDAP (`ldap_config.py`) and SAML (`saml_config.py`) — both configured separately from `configuration.py`. The `users/` app handles profiles and group-based device access permissions.

## Adding a New Device Driver

1. Create a new directory under `switches/connect/`
2. Implement a connector class inheriting from `Connector` (`connect/connector.py`)
3. Add a `CONNECTOR_TYPE_*` constant in `switches/constants.py`
4. Register it in the factory function in `connect/connect.py`
5. Add the type to `Switch.connector_type` choices in `switches/models.py`

See `docs/code/drivers/new-drivers.rst` for detailed guidance.
