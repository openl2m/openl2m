.. image:: ../../_static/openl2m_logo.png

=================
Saving The Config
=================

This functionality is highly vendor driver specific. Drivers should implement this function:

.. code-block:: python

    def save_running_config(self) -> bool:


If changes are made by users, OpenL2M detects that the device driver has implemented this, and make the "Save" button available
by setting *Connector.save_needed = True*

This button is handled in *views.py* by **class SwitchSaveConfig()**