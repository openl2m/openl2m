.. image:: ../_static/openl2m_logo.png

Debugging
=========

When running the built-in web server, and with DEBUG=True in *settings.py*, the code will spit out lots
of debugging information, about what functions are being called, what important stuff they do,
and more. The output shown is produced by inserting lots of calls to *dprint()* in the code.

*dprint()* is defined in switches.utils, and if DEBUG=True will log to the logger configured.

Debugging toolbar
-----------------

We also use the Django Debug Toolbar. See
https://django-debug-toolbar.readthedocs.io/en/latest/installation.html

To enable, add the following to *configuration.py*:

.. code-block:: python3

  DEBUG = True
  DEBUG_TOOLBAR = True
  # where do we allow debug toolbar access from:
  INTERNAL_IPS = [
      '127.0.0.1',        # loopback, eg if on local machine.
      '10.1.1.1',         # a workstation to allow debug from.
      '192.168.1.100',    # another workstation.
      '172.16.1.1',       # third workstation.
  ]


This will now add the toolbar overlay (if you access from the IP list defined about).

Additionally, this url can also be accessed:  *<your-site>/__debug__/*
