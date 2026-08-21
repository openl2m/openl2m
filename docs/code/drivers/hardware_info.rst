.. image:: ../../_static/openl2m_logo.png

====================
Hardware Information
====================

Devices can show information about a variety of hardware. This is intended to show 'stack information'.

We define a *StackMember()* object in *switches/connect/classes.py*. Drivers can create an object,
set the appropriate attributes, and then add this to the *Connector().stack_members* dictionary (with some unique index).

Where It Shows
--------------

This *stack_members* Dict() is shown on the "Device Info" tab, using the template in *templates/_tab_info_general.html*.

.. code-block:: html+django

   {% if connection.stack_members.items %}
   <div class="card border-default mb-2">
   <div class="card-header bg-default">
      <strong>Modules Information</strong>
   </div>
   <div class="card-body">
      {% for dev_id,dev in connection.stack_members.items %}
