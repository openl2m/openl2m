.. image:: ../_static/openl2m_logo.png

Requirements
============

Below are a list of topics that will be helpful if you want to understand
how the OpenL2M project works "under the hood".

**Python 3**

As of v2.4, all the code is written and tested in Python v3.11. Note that Django 5 require v3.10 or above.
There are numerous places to learn this.

The project is by default located in **/opt/openl2m**. To use these scripts, or work on things,
you should first activate the Python virtual environment:

.. code-block:: bash

  $ cd /opt/openl2m
  $ source venv/bin/activate
  (venv) $

Normal Django development steps can now be used.


**Django**

We use the Django web framework, v5.0 or higher. For a good introduction, see
`the Django Tutorial <https://docs.djangoproject.com/>`_
If you follow this tutorial, you will have enough of an Django understanding
to start digging into the code.

E.g. to start the development built-in web server, active the virtual environment, and run:

.. code-block:: bash

  (venv) $ cd openl2m
  (venv) $ python3 manage.py runserver 127.0.0.1:8000


**HTML Layout**

We use `Bootstrap v3.4 for all our HTML layout.
<https://getbootstrap.com/docs/3.4/>`_
A good place to start learning is
`W3Schools. <https://www.w3schools.com/bootstrap/default.asp>`_


**SNMP**

We primarily use the "easysnmp" library, because is it fast. It requires the Net-SNMP
package on your Linux server.
`See these installation docs <https://easysnmp.readthedocs.io/en/latest/>`_

We also use the `pysnmplib library <https://github.com/pysnmp/pysnmp>`_
for a few backend functions where "easysnmp" does not shine. Specifically,
we use *pysnmplib* to manipulate mib entries that are octetstring values representing bitmaps.

This is extensively used in vlan settings. EasySNMP "struggles" with this, as it uses
unicode strings for all internal data representations. Pysnmplib is a pure python implementation
that does not have these problems. However, it is significantly slower, so we only use
it only where absolutely needed. (Note: *pysnmplib* is a continuation of the original *pysnmp*; that
library is no longer developed.)


**Aruba AOS-CX**

We use the *pyaoscx* library `from the github repo <https://github.com/aruba/pyaoscx>`_,
as that frequently provides bugfixes ahead of what is available in the released version available via pip.
See *requirements.txt* for more.


**Netmiko**

`Netmiko <https://github.com/ktbyers/netmiko>`_ is a Python library that
establishes SSH connections to network gear.
`It has a lot of useful functionality.
<https://pynet.twb-tech.com/blog/automation/netmiko.html>`_
We use it for things like device command line execution, and
to provide admin-configurable command line output to users.


**Napalm**

`Napalm <https://napalm-automation.net/>`_ is a Network Automation framework.
In v2.0, we implemented a Napalm interface, in read-only mode, to show how the new API functions.
I.e. this is *purely for demonstration purposes*, and is not heavily tested or used by the developers.
