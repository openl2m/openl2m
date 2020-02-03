.. image:: ../_static/openl2m_logo.png

Requirements
============

Below are a list of topics that will be helpful if you want to understand
how the OpenL2M project works "under the hood".

**Python 3**

All the code is written and tested in Python v3.6. There are numerous places to learn this.

**Django**

We use the Django web framework, v2.2. For a good introduction, see
`the Django Tutorial <https://docs.djangoproject.com/>`_
If you follow this tutorial, you will have enough of an Django understanding
to start digging into the code.

**HTML Layout**

We use `Bootstrap v3.4 for all our HTML layout.
<https://getbootstrap.com/docs/3.4/>`_
A good place to start learning is
`W3Schools. <https://www.w3schools.com/bootstrap/default.asp>`_

**SNMP**

We primarily use the "easysnmp" library, because is it fast. It requires the Net-SNMP
package on your Linux server.
`See these installation docs <https://easysnmp.readthedocs.io/en/latest/>`_

We also use the `pysnmp library <http://snmplabs.com/pysnmp/>`_
for a few backend functions where "easysnmp" does not shine. Specifically,
we use pysnmp to manipulate mib entries that are octetstring values representing bitmaps.
This is extensively used in vlan settings. EasySNMP "struggles" with this, as it uses
unicode for all internal data representations. Pysnmp is a pure python implementation
that does not have these problems. However, it is significantly slower, so we only use
it only where absolutely needed.


**Netmiko**

`Netmiko <https://github.com/ktbyers/netmiko>`_ is a Python library that
establishes SSH connections to network gear.
`It has a lot of useful functionality.
<https://pynet.twb-tech.com/blog/automation/netmiko.html>`_
We use it to do what we cannot accomplish via SNMP, such as switch command line execution,
to provide admin-configurable command line output to users.
