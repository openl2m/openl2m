.. image:: ../../_static/openl2m_logo.png

===================
Admin API Endpoints
===================

This is the list of Admin REST API endpoints, and their functionality.

**A simple Python example API client is provided at** https://github.com/openl2m/api_client

.. list-table:: Admininstrative REST API endpoints
    :widths: 25 15 15 15 100 100
    :header-rows: 1

    * - Endpoint
      - GET
      - POST
      - PATCH
      - Parameters
      - Description
    * - api/admin/users/
      - Yes
      -
      -
      -
      - Get all user accounts.
    * - api/admin/users
      -
      - Yes
      -
      - username (str), password(str), other as needed.
      - Add a new user account.
    * - api/admin/users/<id>/
      - Yes
      -
      -
      - id(int)
      - Get user account information for the given user id.
    * - api/admin/users/<id>/
      -
      - Yes
      - Yes
      - as needed.
      - Update the user attributes for the given user id.
    * - api/admin/switches/
      - Yes
      -
      -
      -
      - Get a list of all switches (devices).
    * - api/admin/switches/
      -
      - Yes
      -
      - as needed (TBD)
      - Add a new switch (device)
    * - api/admin/switches/<id>/
      - Yes
      -
      -
      -
      - Get details about this specific switch (device).
    * - api/admin/switches/<id>/
      -
      - Yes
      - Yes
      - as needed
      - Update the attributes of a giving Switch object.
    * - api/admin/switches/switchgroups/
      - Yes
      -
      -
      -
      - Get a list of all switch groups.
    * - api/admin/switches/switchgroups/
      -
      - Yes
      -
      - as needed (TBD)
      - Add a new switch group.
    * - api/admin/switches/switchgroups/<id>/
      - Yes
      -
      -
      -
      - Get details about this specific switch group.
    * - api/admin/switches/switchgroups/<id>/
      -
      - Yes
      - Yes
      - as needed
      - Update the attributes of a giving switch group object.
    * - api/admin/switches/snmpprofiles/
      - Yes
      -
      -
      -
      - Get a list of all snmp profiles.
    * - api/admin/switches/snmpprofiles/
      -
      - Yes
      -
      - as needed (TBD)
      - Add a new snmp profile.
    * - api/admin/switches/snmpprofiles/<id>/
      - Yes
      -
      -
      -
      - Get details about this specific snmp profile.
    * - api/admin/switches/snmpprofiles/<id>/
      -
      - Yes
      - Yes
      - as needed
      - Update the attributes of a giving snmp profile.
    * - api/admin/switches/netmikoprofiles/
      - Yes
      -
      -
      -
      - Get a list of all credential (netmiko) profiles.
    * - api/admin/switches/netmikoprofiles/
      -
      - Yes
      -
      - as needed (TBD)
      - Add a new credential (netmiko) profile.
    * - api/admin/switches/netmikoprofiles/<id>/
      - Yes
      -
      -
      -
      - Get details about this specific credential (netmiko) profile.
    * - api/admin/switches/netmikoprofiles/<id>/
      -
      - Yes
      - Yes
      - as needed
      - Update the attributes of a giving netmiko (credential) profile.

