.. image:: ../_static/openl2m_logo.png

==========================
Adding Arista eAPI Devices
==========================

Prerequisites
-------------

* Create a Credential Profile with the proper username / password that will be used
  to access this device via the eAPI.
* As needed, create Commands and Command Groups to assign to this device.


Configuration
-------------

Arista switches can be managed via the device REST API.  You will need to configure the switch to allow this access.
Something like this is needed as a base config. We recommend only running over the https port (using TLS).

.. code-block:: bash

    switch(config)# management api http-commands
    switch(config-mgmt-api-http-cmds)# no shutdown
    switch(config-mgmt-api-http-cmds)# protocol https
    switch(config-mgmt-api-http-cmds)# no protocol http

    # you should consider securing this with an ACL, e.g.
    vrf MGMT
      no shutdown
      ip access-group YOUR_MANAGEMENT_ACL


Please refer to your Arista eAPI documentation for more.
A good place to start is  https://arista.my.site.com/AristaCommunity/s/article/arista-eapi-101

.. note::

    If you get the error **"401 Client Error: Unauthorized for url"**, this means that your OpenL2M server ip is not
    permitted on the web server acl "YOUR_MANAGEMENT_ACL"



Connection Configuration
------------------------

**Connector Type:** set to **Arista eAPI** for Arista switches supported via the eAPI REST API.

**SNMP Profile:** this is a don't care field.

**Credentials Profile:** Select the proper profile that stores the REST API credentials.
Note that these same credentials are used for any Commands applied to this device,
as these commands are also executed through the API (ie. not over SSH!).


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !



