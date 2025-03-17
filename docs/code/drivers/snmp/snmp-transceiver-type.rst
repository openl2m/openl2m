.. image:: ../../../_static/openl2m_logo.png

=========================
Discover interface optics
=========================

The MAU (Media Access Unit) mib is the standard way of describing media types, ie. transceivers.
See https://mibs.observium.org/mib/MAU-MIB/

We call _get_interface_transceiver_types() to read the device mib at **ifMauType** (.1.3.6.1.2.1.26.2.1.1.3).
This is parsed in *_parse_mibs_if_mau_type()* Here we read the return value,
and this is parsed to an optic or transceiver type in *_parse_and_set_mau_type()*

"Interesting" types are defined in snmp/constants.py, the variable *mau_types*. We primarily want to show optical transceivers.
If a type of interest is present, we then assign a Transceiver() object to the Interface().
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

E.g.  .1.3.6.1.2.1.26.2.1.1.3.1.1 = OID: .1.3.6.1.2.1.26.4.35

1.1 is <if_index>.<sub-port>, ie the first interface. .1.3.6.1.2.1.26.4.35 is "10GBASE-LR"


