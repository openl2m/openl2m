.. image:: ../_static/openl2m_logo.png

=============
API Endpoints
=============

This is the list of REST API endpoints, and their functionality.

*<group>* and *<switch>* are the ID's as retrieved from the 'menu' call at *api/switches/*

**API calls that succeed** will return an **HTTP code 200**, and typically a "reason" JSON return variable.

**API calls that fail** will return a 4xx code. This can be 403 (forbidden, ie. access denied),
400 for badly formed requests, or other 400-level codes. Typically, there is a "reason" JSON return variable
with more information on the failure.


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
    * - api/switches/interface/vlan/<group>/<switch>/<interface>/
      - No
      - Yes
      - vlan(int)
      - Set the untagged vlan on an interface.
    * - api/switches/interface/state/<group>/<switch>/<interface>/
      - No
      - Yes
      - state(str), "on,enabled,enable,yes,y,1" for UP, else DOWN
      - Set the administrative state of an interface.
    * - api/switches/interface/poe_state/<group>/<switch>/<interface>/
      - No
      - Yes
      - poe_state(str), "on,enabled,enable,yes,y,1" for UP, else DOWN
      - Set the PoE state of an interface.
    * - api/switches/interface/description/<group>/<switch>/<interface>/
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
    * - api/users/token/
      - No
      - Yes
      - username(str), password (str)
      - Create an API token.


.. note::

  All API calls that change a setting will **fail** if you are trying to set the current state!
  I.e. if you enable an interface that is already enabled, the API will return a HTTP 404 error.
  Likewize for PoE state, Vlan and Description.


.. note::

  Most endpoints that require POST variables, will return a descriptive error if improper parameters are passed in.


Below is an example of the "Save Config" API call, where the 'save' parameter is missing.

.. code-block::

  http --form POST  https://<domain_name>/api/switches/save/35/272/ 'Authorization: Token <your-token-string-here>'
  HTTP/1.1 400 Bad Request
  Allow: POST, OPTIONS
  ...
  {
      "reason": "Missing required parameter and value: 'save=yes'"
  }
