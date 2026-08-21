.. image:: ../../_static/openl2m_logo.png

=============
Show Warnings
=============

Drivers can add warnings to show in the "Warnings/Errors" tab.

.. code-block:: python

    self.add_warning("Warning !!!")


This function is implemented in the *base Connector()* class, and adds to the *self.warnings* List().


Where It Shows
--------------

This *self.warnings* List() is shown on the "Device Info" tab, using the template in *templates/_tab_warnings.html*.
