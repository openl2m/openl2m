.. image:: ../../../_static/openl2m_logo.png

=========================
Discover interface optics
=========================

Using MAU-MIB
-------------

The MAU (Media Access Unit) mib is the standard way of describing media types, ie. transceivers.
See https://mibs.observium.org/mib/MAU-MIB/

This mib defines transceiver types for interface indeces. These types are defines as 'OID' formatted strings.
E.g. a value of ".1.3.6.1.2.1.26.4.35" means a 10GBase-LR optical transceiver.

We call _get_interface_transceiver_types() to read the device mib at **ifMauType** (.1.3.6.1.2.1.26.2.1.1.3).
This is parsed in *_parse_mibs_if_mau_type()* Here we read the return value,
and this is parsed to an optic or transceiver type in *_parse_and_set_mau_type()*

"Interesting" types are defined in snmp/constants.py, the variable *mau_types*. We primarily want to show
optical transceivers. If a type of interest is present, we then assign a Transceiver() object to the Interface().
This is then displayed in the template *_tpl_if_type_icons.html*

.. code-block:: jinja

    {% if iface.transceiver %}
    &nbsp;
    <i class="fas fa-bolt" aria-hidden="true"
        data-bs-toggle="tooltip"
        title="{{ iface.transceiver }} transceiver">
    </i>
    {% endif %}


**Note:** The return value are numbers defined by IANA in https://www.iana.org/assignments/ianamau-mib/ianamau-mib
and # https://datatracker.ietf.org/doc/html/rfc3636 .

They indicate the transceiver type. All valid returns start with ".1.3.6.1.2.1.26.4."

E.g.  .1.3.6.1.2.1.26.2.1.1.3.24.1 = OID: .1.3.6.1.2.1.26.4.35

24.1 is <if_index>.<sub-port>, ie interface 24. The return value *".1.3.6.1.2.1.26.4.35"* is *"10GBASE-LR"*,
per the definitions in the IF-MAU MIB.


.. note::

    Some drivers augment or override the _get_interface_transceiver_types() call to run their own discovery.


Other thoughs
-------------

**Not Implemented Yet**

We can also look at this:
entPhysicalClass (.1.3.6.1.2.1.47.1.1.1.1.5) for values 10 (Port)

    .1.3.6.1.2.1.47.1.1.1.1.5.1006 = INTEGER: 10


followed by:

Use 'entPhysicalDescr ('.1.3.6.1.2.1.47.1.1.1.1.2')
    .1.3.6.1.2.1.47.1.1.1.1.2.1006 = STRING: "Gigabit Ethernet Port"
    .1.3.6.1.2.1.47.1.1.1.1.2.1007 = STRING: "SFP-10Gbase-SR"

*Some* implementation show the optics type in the device description, *but not all!*

The interface index 1006 is type .1.3.6.1.4.1.9.12.3.1.10.151
and interface 1007 is type .1.3.6.1.4.1.9.12.3.1.9.76.3, defined as SFP10GSR
See https://oid-base.com/get/1.3.6.1.4.1.9.12.3.1.9.76.3

entPhysicalVendorType (.1.3.6.1.2.1.47.1.1.1.1.3) can also be used:
    .1.3.6.1.2.1.47.1.1.1.1.3.1006 = OID: .1.3.6.1.4.1.9.12.3.1.10.151
    .1.3.6.1.2.1.47.1.1.1.1.3.1007 = OID: .1.3.6.1.4.1.9.12.3.1.9.76.3

Note that the returned value is *vendor-defined*, i.e. complex to parse!