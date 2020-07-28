.. image:: ../../_static/openl2m_logo.png


===========
Connections
===========

Switch connections are via SNMP. All functions for connections is in the
"switches/connect/" directory.

**connector.py**

This contains the *Connector()* base class that all connectors inherit from:



**connect.py**

get_connection_object() figures out what specific Connector() class to get for the device.
It returns the proper object.

It should be called as:

.. code-block:: bash

  try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        # handle exception as needed


**snmp.py**
The base class for SNMP connectors is the SnmpConnector() class, defined in switches/connect/snmp.py
This is the base class that implements all high-level functions to talk to switches.

See :doc:`SNMP Connector <snmp>`
