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
      - GET all user accounts.
    * - api/admin/users
      -
      - Yes
      -
      - username (str), password(str), other as needed.
      - Add a new user account.
    * - api/users/<id>/
      - Yes
      -
      -
      - id(int)
      - Get user account information for the given user id.
    * - api/users/<id>/
      -
      - Yes
      - Yes
      - as needed.
      - Update the user attributes for the given user id.
