.. image:: _static/openl2m_logo.png

===============
Troubleshooting
===============

Here are various items that may help with troubleshooting OpenL2M configuration and installation.


SNMP Fails for All Devices
--------------------------

**IF ALL YOUR SNMP DEVICES FAIL**, there could be a problem with the installation of the EzSNMP package!

The EzSNMP installer provides pre-built binaries for as many Python and Linux distros as possible.
This sometimes fails. If you have problems with all your SNMP devices not authenticating,
you can force a re-installation of EzSNMP with the following commands. This should fix an incorrect installation.

.. code-block:: bash

  systemctl stop openl2m
  source /opt/openl2m/venv/bin/activate     # active the virtual environment
  pip3 install --force-reinstall --no-binary :all: ezsnmp
  deactive
  systemctl start openl2m

See more at https://carlkidcrypto.github.io/ezsnmp/html/index.html

