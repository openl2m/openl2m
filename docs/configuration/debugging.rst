.. image:: ../_static/openl2m_logo.png

=========
Debugging
=========

Debugging is mostly to assist the developers with troubleshooting. This can
come in handy when you have a new device that is not properly rendering.

The source uses the *dprint(<string>)* function to print debugging output.
If *settings.DEBUG* is enabled, this will output to the *openl2m.console* Python logger.

To enable lots of debugging output, add the following to the
configuration file in *openl2m/configuration.py*

This configuration below enables the following debugging, depending on *handler* chosen:

* *file* output goes to /tmp/openl2m-debug.log. Modify this path as needed.
  This implementents time-based rotation, with a new log every day. You can also change
  to size-based rotation. See the Python 3 logging docs for more details.
* *console* goes to the console screen. Use this when using 'django runserver' for testing.
* *syslog* goes to a configured local syslog receiver.
* you can also log to remote syslog, Sentry.io, or anything else supported by the
  Python logging library. Further configuration is left as an exercise to the reader.

Add this to configuration.py:

.. code-block:: bash

  # logging for debug:
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
          'minimal': {
              # very minimal format:
              'format': '[OpenL2M] %(message)s',
          },
          'standard': {
              'format' : "[OpenL2M] [%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
              'datefmt' : "%d/%b/%Y %H:%M:%S"
          },
          'console': {
              # very minimal format for console:
              'format': '%(asctime)s %(message)s',
          },
          'basic': {
              # basic format:
              'format': '%(asctime)s %(levelname)s %(message)s',
          },
      },
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
              'formatter': 'console',
          },

          'file': {
              'level': 'DEBUG',
              'class': 'logging.handlers.TimedRotatingFileHandler',
              'formatter': 'basic',
              'when': 'd',            # rotate daily
              'backupCount': 14,      # keep max 14 days of files
              'filename': '/tmp/openl2m-debug.log',
          },
          'syslog': {
              'class': 'logging.handlers.SysLogHandler',
              'formatter': 'standard',
              'facility': 'user',
              # uncomment next line if rsyslog works with unix socket only (UDP reception disabled)
              #'address': '/dev/log'
          }
      },
      'loggers': {
          # NOTE: if using Celery, do NOT use file, but only console and/or syslog!
          'openl2m.console': {
              'handlers': ['console'],
              'level': 'DEBUG',
          },
      },
  }


Alternatively, you can use a syslog config, or the like, that does NOT write files directly.
See more at https://docs.djangoproject.com/en/3.2/topics/logging/

**Don't forget to remove this configuration when you are done!** (and start Celery, if needed)
