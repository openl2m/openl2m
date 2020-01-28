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
* This implementents time-based rotation, with a new log every day. You can also change
  to size-based rotation. See the Python 3 logging docs for more details.
* if running in DEBUG mode (for developers), the same output also goes to
  the console screen.
* you can also log to syslog, Sentry.io, or anything else supported by the
  Python logging library. Configuration is left as an exercise to the reader.

Add this to configuration.py:

.. code-block:: bash

  # logging for debug:
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
          'console': {
              # very minimal format:
              'format': '%(asctime)s %(message)s',
          },
          'file': {
              # basic format:
              'format': '%(asctime)s %(levelname)-8s %(message)s',
          }
      },
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
              'formatter': 'console',
          },
          'file': {
              'level': 'DEBUG',
              'class': 'logging.handlers.TimedRotatingFileHandler',
              'formatter': 'file',
              'when': 'd',            # rotate daily
              'backupCount': 14,      # keep max 14 days of files
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
          },
      },
  }

NOTE: this is NOT compatible with running the Celery task engine.
If you have this enabled, for debugging please stop that process:

.. code-block:: bash

  sudo systemctl stop celery

Alternatively, you can use a syslog config, or the like, that does NOT write files directly.

**Don't forget to remove this configuration when you are done!** (and start Celery, if needed)
