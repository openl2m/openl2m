.. image:: ../../_static/openl2m_logo.png

=============
Adding Syslog
=============

Devices can show syslog entry information that will be added to the "Recent Syslog Entries" section of the "Device Information" tab.

Drivers are responsible for adding *class SyslogMsg()* objects to the *Connector.syslog_msgs* Dict().

.. code-block:: python

   # Connector() class syslog attribute defined around line 198 in switches/connect/connector.py
   self.syslog_msgs: dict[int, SyslogMsg] = {}  # list of Syslog messages, if any


Where It Shows
--------------

This *self.syslog_msgs* data is shown on the "Device Info" tab, using the template in *templates/_tab_info_general.html*, starting around line 24

.. code-block:: html+django

   {% if connection.syslog_msgs.items %}
   <div class="card border-default mb-2">
   <div class="card-header bg-default">
      <strong>Recent Syslog Entries ({{ connection.syslog_max_msgs }} max)</strong>
   </div>
   <div class="card-body">
         <div class="fw-bold border-bottom pb-1 mb-1 row">
         <div class="col-3">Approx. Time</div>
         <div class="col">Message</div>
         </div>
         {% for index,msg in connection.syslog_msgs.items %}


