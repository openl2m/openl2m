.. image:: ../_static/openl2m_logo.png

==============
API User Token
==============

The "User Token" endpoint allows a user to create a REST token by POSTing username and password.
However, we recommend you use the WebUI to create your tokens.

.. code-block:: bash

     http --form POST http://<your-domain>/api/users/token/ username=<username> password=<password>


Output
------

The output will look something like below.
Since this endpoint is actually implemented by the Django Rest Framework, this may change!

.. code-block:: bash

    HTTP/1.1 200 OK
    Allow: POST, OPTIONS
    Content-Type: application/json
    ...
    {
        "email": "user.name@your-domain.com",
        "token": "493817558ac01ca624768ab65d07b43f0cf4ebf4",
        "user_id": 23
    }
