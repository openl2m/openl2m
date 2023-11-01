.. image:: ../_static/openl2m_logo.png

=============
API Endpoints
=============

This is the list of REST API endpoints, and their functionality.

.. list-table:: API endpoints
    :widths: 25 15 15 100 100
    :header-rows: 1

    * - Endpoint
      - GET
      - POST
      - Parameters
      - Description
    * - api/
      - Yes
      - No
      -
      - Browsable API interface if Web UI session exists.
    * - api/token/
      - No
      - Yes
      - username(str), password(str)
      - Get an API token.
    * - api/stats/
      - Yes
      - No
      -
      - Get some statistics about OpenL2M usage.
    * - api/switches/
      - Yes
      - No
      -
      - Get list of allowed devices
    * - api/switches/basic/<group>/<switch>/
      - Yes
      - No
      -
      - Get the basic device view
    * - api/switches/details/<group>/<switch>/
      - Yes
      - No
      -
      - Get the details device view (ie. add arp, lldp, etc.)
    * - api/switches/add_vlan/<group>/<switch>/
      - No
      - Yes
      - vlan_name(str), vlan_id(int)
      - Add a vlan to the device.
    * - api/switches/vlan/<group>/<switch>/<interface>/
      - No
      - Yes
      - vlan(int)
      - Set the untagged vlan on an interface.
    * - api/switches/state/<group>/<switch>/<interface>/
      - No
      - Yes
      - state(str), "on,enabled,enable,yes,1" for UP, else DOWN
      - Set the administrative state of an interface.
    * - api/switches/poe_state/<group>/<switch>/<interface>/
      - No
      - Yes
      - poe_state(str), "on,enabled,enable,yes,1" for UP, else DOWN
      - Set the PoE state of an interface.
    * - api/switches/description/<group>/<switch>/<interface>/
      - No
      - Yes
      - description(str)
      - Set the description on an interface.
