.. image:: ../../_static/openl2m_logo.png

===============
Add Log Entries
===============

Drivers can add entries to show in the "Activity Logs" tab.

.. code-block:: python

    # see switches/connect/connector.py, around line 2054
    def add_log(self, description: str, type: int, action: int, if_name: str = "", if_index: int = 0):

This adds a *Log()* object that is defined in *switches/models.py*, and stored in the database,
indexed to the device, interface (if given), and user. It is appropriately time-stamped.


Where It Shows
--------------

The most recent *Log()* entries for a device (Switch() object) are shown on the "Activity Logs" tab,
created in the template at *templates/_tab_logs.html*.

.. note::

    This tab only shows changes, warnings and error log entries. I.e. it does not show users simply viewing a device!


Full logs can be seen by admins from the User Menu drop down, and from user info pages.
