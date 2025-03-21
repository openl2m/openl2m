.. image:: ../../../../_static/openl2m_logo.png


================================
Cisco SNMP Transceiver Discovery
================================


On some (older?) devices the CISCO-STACK-MIB can be used to discover the transceiver type of an interface.

The **portType** (.1.3.6.1.4.1.9.5.1.4.1.1.5) returns a number for the type of interface this "stack index" is.
(Note: our code calls this ciscoPortType)

We define a number of "interesting" interface types in *cisco_port_types{}*. If an interesting type is found, we store
it in *self.cisco_port_type_by_stack_id{}*, keyed on the "stack index".

We can then read **portIfIndex** (.1.3.6.1.4.1.9.5.1.4.1.1.11) to map the "stack index" to a SNMP interface id "ifIndex".
(Note: our code calls this ciscoPortIfIndex).
We check to see if we found an interesting interface type for this stack index (in the above dict),
and then attach the Transceiver() info found above to the Interface() for the correspoding ifIndex.

