.. image:: ../../_static/openl2m_logo.png

=================
Other Information
=================

Devices can show other information that will be added to the "General Information" section of the "Device Information" tab.

The 'System' sub-heading exists by default, and other sub-headings can be added as shown:

.. code-block:: python

   # this adds to the default sub-heading
   self.add_more_info("System", "Something", "Interesting Data For The User")
   # create a new sub-heading
   self.add_more_info("Old Hardware", "Field Name", "Field Information Here!")

This is implemented in the base Connector() class, and added entries to the *self.more_info* entry, which is a Dict() of Dict().
The top-level Dict() is keyed by the sub-category name (e.g. "System"), the second level by the field (e.g. "Something")


Where It Shows
--------------

This *self.more_info* data is shown on the "Device Info" tab, using the template in *templates/_tab_info_general.html*, starting around line 4

.. code-block:: html+django

   <div class="card border-default mb-2">
   <div class="card-header bg-default">
      <strong>General Information</strong>
   </div>
   <div class="card-body">
      {% for category,values in connection.more_info.items %}


