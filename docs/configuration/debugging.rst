.. image:: ../_static/openl2m_logo.png

=========
Debugging
=========

Debugging is mostly to assist the developers with troubleshooting. This can
come in handy when you have a new device that is not properly rendering.

To enable lots of debugging output, at the following to the file
configuration file in *openl2m/configuration.py*

This configuration below enables the following debugging:

* Debug output goes to /tmp/openl2m-debug.log. Modify this path as needed.
* if running in DEBUG mode (for developers), the same output also goes to
  the console screen

Configure this:

.. code-block:: bash

  # logging for debug:
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
          },
          'file': {
              'level': 'DEBUG',
              'class': 'logging.FileHandler',
              'filename': '/tmp/openl2m-debug.log',
          },
      },
      'loggers': {
          'openl2m.console': {
              'handlers': ['console'],
              'level': 'DEBUG',
          },
          'openl2m.debug': {
              'handlers': ['file'],
              'level': 'DEBUG',
          }
      },
  }


Don't forget to remove this when you are done!
