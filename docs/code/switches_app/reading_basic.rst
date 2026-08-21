.. image:: ../../_static/openl2m_logo.png

======================
Reading Interface Data
======================

The **class SwitchBasics()** is called when reading the basic info of a device.
This calls **switch_view()** to handle the data gathering and rendering (as does the detailed info page, see next).


**switch_view()**

1 - Creates the Connector() object:

.. code-block:: python

  conn = get_connection_object(request, group, switch)


2 - Next, gets the basic switch information. This reads Interface, Vlan, and Power-over-Ethernet data::

.. code-block:: python

   conn.get_switch_basic_info()

Once the device has been read, this data is cached in the user session. On subsequent views, the cached data is used.
E.g. you read the basic layout, then disable an interface, and go back to the main switch page.
That second time around, the cached data will be used.

3 - Optional, read hardware info. This is actually handled in *get_switch_basic_info()* above.

It checks to see if *get_my_hardware_details()* is implemented, and calls it.

.. code-block:: python

   conn.get_my_hardware_details()


Drivers need to implement this function call if hardware info is desired.

.. note::

   Reading hardware info can be disabled globally in settings.py,
   or in the SwitchGroup() or Switch() admin pages.


4 - If command parameters are POST-ed, then this is handled. See in the next few pages.

5 - Finally, we call the Django *render()* function, with the *conn Connector()* object (and a few other variables).
   The *templage_name* variable point to the correct high-level template, depending on Basic or Details view.
   This then renders the HTML page