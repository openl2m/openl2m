.. image:: ../_static/openl2m_logo.png

===========================
Adding Aruba AOS-CX Devices
===========================

Prerequisites
-------------

* Create a Credential Profile with the proper username / password that will be used to manage this device.
* As needed, create Commands and Command Groups to assign to this device.

Switch Configuration
--------------------

AOS-CX switches are managed via the device REST API. Minimal supported firmware is v10.09.
Our driver will automatically use the last API version availabe on the device.

You will need to configure the switch to allow this access.
See more details at https://developer.arubanetworks.com/aoscx/docs/introduction

Something like this is needed:

.. code-block:: bash

    switch(config)# https-server rest access-mode read-write
    switch(config)# https-server vrf default
    OR:
    switch(config)# https-server vrf mgmt

    and then set an admin username and password.


Validate that the REST server is running with the following command. You should see similar output:

.. code-block::

    show https-server

        HTTPS Server Configuration
        ----------------------------
        VRF                      : default, mgmt
        REST Access Mode         : read-write
        Max sessions per user    : 6
        Session idle timeout     : 20
        Session absolute timeout : 480

Note that read-write access is the default. You can explicitly set this, if needed,
with "https-server rest access-mode read-write"

Please refer to your Aruba AOX-CX documentation for more.


REST API Troubleshooting
------------------------

In case this is needed, here are some commands that can help troublehoot REST configurations.

View REST session events, and logins:

.. code-block::

    show events -r | include restd



Connection Configuration
------------------------

**Connector Type:** set to **Aruba AOS-CX** for Aruba switches supported via the AOS-CX REST API.

**SNMP Profile:** this is a don't care field.

**Credentials Profile:** Select the proper profile that stores the REST API credentials.
Note that these same credentials used for any Commands applied to this device.


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !


