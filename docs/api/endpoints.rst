.. image:: ../_static/openl2m_logo.png

=============
API Endpoints
=============

This is the list of REST API endpoints, and their functionality.

*<group>* and *<switch>* are the ID's as retrieved from the 'menu' call at *api/switches/*

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
      - Get list of allowed devices (ie. the 'menu')
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
    * - api/switches/vlan/<group>/<switch>/<interface>/
      - No
      - Yes
      - vlan(int)
      - Set the untagged vlan on an interface.
    * - api/switches/state/<group>/<switch>/<interface>/
      - No
      - Yes
      - state(str), "on,enabled,enable,yes,y,1" for UP, else DOWN
      - Set the administrative state of an interface.
    * - api/switches/poe_state/<group>/<switch>/<interface>/
      - No
      - Yes
      - poe_state(str), "on,enabled,enable,yes,y,1" for UP, else DOWN
      - Set the PoE state of an interface.
    * - api/switches/description/<group>/<switch>/<interface>/
      - No
      - Yes
      - description(str)
      - Set the description on an interface.
    * - api/switches/save/<group>/<switch>/
      - No
      - Yes
      - save(str), "on,enabled,enable,yes,y,1"
      - Save the configuration of the device.
    * - api/switches/vlan/add/<group>/<switch>/
      - No
      - Yes
      - vlan_name(str), vlan_id(int)
      - Add a vlan to the device.
    * - api/switches/vlan/edit/<group>/<switch>/
      - No
      - Yes
      - vlan_name(str), vlan_id(int)
      - Edit the name of a vlan on the device.
    * - api/switches/vlan/delete/<group>/<switch>/
      - No
      - Yes
      - vlan_id(int)
      - Delete a vlan from the device.
