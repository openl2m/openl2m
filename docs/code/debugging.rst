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

To enable,

1 - add to *local_requirements.txt*:

.. code-block:: bash

  django-debug-toolbar

and then run *./upgrade.sh*

2 - add the following to *configuration.py*:

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


"Developer Mode"
----------------

There is an extra 'setting' that can be added to your *configuration.py* to enable DEVELOPER mode. If enabled,
this adds the 'django-extensions' module to the configured Django apps. This gives us a lot of extra tools.

We use this primary to generate images representing our various data Models.

To enable:

1 - install the GraphViz package at the OS level. Something like:

.. code-block:: bash

  sudo apt-get install graphviz graphviz-dev

2 - add the graphviz and django-extensions Python package to your *local_requirements.txt*:

.. code-block:: bash

  django-extensions
  pygraphviz

and then run *./upgrade.sh*

3 - add this to *configuration.py*:

.. code-block:: python

  # if this is True, then we add some extra "stuff", such as 'django-extension' for documentation, etc.
  DEVELOPER = True

Now, all the options from 'django-extensions' are available.
See more at https://django-extensions.readthedocs.io/en/latest/index.html
