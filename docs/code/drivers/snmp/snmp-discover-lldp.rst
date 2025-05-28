.. image:: ../../../_static/openl2m_logo.png

======================
LLDP Neigbor Discovery
======================

*_get_lldp_data(self)* is called to read LLDP Neigbor info.
We read this from the SNMP LLDP-MIB *lldpRemTable* with entries
located in **lldpRemEntry** at *.1.0.8802.1.1.2.1.4.1.1*

Entry Indexing
--------------

These *lldpRemEntry* items are indexed by  <lldpRemTimeMark>.<lldpRemLocalPortNum>.<lldpRemIndex>

As seen in the LLDP-MIB:

.. code-block:: bash

    lldpRemEntry:
    INDEX {
            lldpRemTimeMark,
            lldpRemLocalPortNum,
            lldpRemIndex
        }

**lldpRemLocalPortNum** is of type *LldpPortNumber*, and  identifies the port on which the remote system information is received.

Again, from the MIB:

.. code-block:: bash

    LldpPortNumber ::=
        "Each port contained in the chassis (that is known to the
        LLDP agent) is uniquely identified by a port number.

        A port number has no mandatory relationship to an
        InterfaceIndex object (of the interfaces MIB, IETF RFC 2863).
        If the LLDP agent is a IEEE 802.1D, IEEE 802.1Q bridge, the
        LldpPortNumber will have the same value as the dot1dBasePort
        object (defined in IETF RFC 1493) associated corresponding
        bridge port.  If the system hosting LLDP agent is not an
        IEEE 802.1D or an IEEE 802.1Q bridge, the LldpPortNumber
        will have the same value as the corresponding interface's
        InterfaceIndex object.

        Port numbers should be in the range of 1 and 4096 since a
        particular port is also represented by the corresponding
        port number bit in LldpPortList."

This means that *lldpRemLocalPortNum* is the Q-BRIDGE <port-id>, mapped back to the *ifIndex*
from MIB-II in *self.qbridge_port_to_if_index[port_id]*

If Q-BRIDGE is NOT implemented, <port-id> = *ifIndex*, ie without the mapping.


*lldpRemTimeMark* and *lldpRemIndex* are irrelevant for our needs, but the combination of all 3 indeces is used as the 'key' to storing the NeighborDevice() object on an Interface()


Entry Attributes
----------------

Each entry is sequence of attributes, all indexed as described above. We read and store the following:

**lldpRemPortId** - a value describing the remote connected port name. Interpretation of this field depends on the value of lldpRemPortIdSubType.

**lldpRemPortIdSubtype** - a value indicating how the interpret lldpRemPortId. We think we can interpret these as strings:
    LLDP_PORT_SUBTYPE_INTERFACE_ALIAS, LLDP_PORT_SUBTYPE_MAC_ADDRESS, LLDP_PORT_SUBTYPE_NETWORK_ADDRESS, LLDP_PORT_SUBTYPE_INTERFACE_NAME
    For all other values, we set the remote port name field to empty ""

**lldpRemPortDesc** - the remote port's description

**lldpRemSysName** - the remote system name

**lldpRemSysDesc** - the remote system description, frequently the firmware version or OS info.

**lldpRemSysCapEnabled** - a bit-mapped field showing the current enabled capabilities of the remote device. E.g. wifi, telephone, router/switch, etc.

**lldpRemChassisIdSubtype** - what the chassis id means, ie how to interpret the data, eg as a string, ethernet address, ipv4/6 address.

**lldpRemChassisId** - the remote chassis id.(see above)


Attribute Parsing
-----------------

Parsing is handled in *switches/connect/snmp/connector.py*, function *_parse_mibs_lldp()* around line 2500.

If we receive the following SNMP data:

..code-block:: text

    **.1.0.8802.1.1.2.1.4.1.1.8**.405.12.1 = "Uplink Port"

We parse **.1.0.8802.1.1.2.1.4.1.1.8** to be **lldpRemPortDesc**. This then gives an index of *405.12.1*

Per the above, this means the interface <port_id> = 12, which can be mapped to an Interface().
For that interface, we can then set the *NeighborDevice().port_descr* = <return value> = "Uplink Port"

This parsing is implemented for all attributes listed above.


Management Address
------------------

We may be able to read a device management address from **lldpRemManAddrIfSubtype** (.1.0.8802.1.1.2.1.4.2.1.3)

This entry is parsed in *_parse_mibs_lldp_management()*. This OID returned is a long entry starting with *lldpRemManAddrIfSubtype*,
followed by the 3 digits "lldp index".

This lldp-index then is followed by the OID representation of the management IP address. This consists of <address-type>.<length>.<ip address in dotted-decimal format>,
identical to how this is encoded in the ARP/ND tables at *ipNetToPhysicalPhysAddress*

Example: we read the OID *.1.0.8802.1.1.2.1.4.2.1.3.0.142.1.1.4.10.128.8.66* = 2

This is lldpRemManAddrIfSubtype.<0.142.1>.<1>.<4>.<10.128.8.66>

Ie. the device with lldp-index "0.142.1" has an IPv4 (1) address of length 4, and value "10.128.8.66"

We then set *NeighborDevice().management_address* and *.management_address_type* accordingly!



