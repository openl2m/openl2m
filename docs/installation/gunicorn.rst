.. image:: ../_static/openl2m_logo.png

=====================
Gunicorn Installation
=====================

OpenL2M is developed and tested running as an application under the gunicorn_ WSGI service. This basically runs the OpenL2m Python code as a service process
with a WSGI interface. The Nginx web server talks in the backend to this WSGI interface to render client http requests.
Gunicorn is started as a service from systemd. (Note that Apache web server should work fine, but is left as an exercise to the reader.)

.. _gunicorn: http://gunicorn.org/


The gunicorn program was installed during the OpenL2M installation (in the Python Virtual environment).
You need to copy the Gunicorn configuration into the "root" openl2m installation path as `gunicorn_config.py`
(e.g. `/opt/openl2m/gunicorn_config.py` per our example installation).

.. code-block:: bash

  cp /opt/openl2m/scripts/gunicorn_config.py /opt/openl2m/gunicorn_config.py

Modify this file as needed for your environment.
Note the following:

* If you change the service port from 8001, you will also need to change the
  corresponding nginx configuration (see later on)!

* The number of workers is related to how many users your site will service at the same time.
  If this is large, increase the 3 to something higher, and restart the service (see below)

* The timeout is increased from the default 30 seconds, to 150. This is to allow large switch stacks to be polled
  without causing a process timeout. You may need to adjust this timeout to suit your environment.

**systemd configuration**

We will install Gunicorn as a service under systemd. The systemd service definition is in the file 'openl2m.service'.

Copy the file *openl2m.service* to the */etc/systemd/system* directory:

.. code-block:: bash

  # cp ./scripts/openl2m.service /etc/systemd/system

Now activate this service:

.. code-block:: bash

  sudo systemctl daemon-reload
  sudo systemctl start openl2m
  sudo systemctl enable openl2m

And verify:

.. code-block:: bash

  sudo systemctl status openl2m

  This should return several lines, indicating the service is running. It should end with something similar to this:

.. code-block:: bash

  CGroup: /system.slice/openl2m.service
          ├─1008503 /opt/openl2m/venv/bin/python3 /opt/openl2m/venv/bin/gunicorn --pid /var/tmp/openl2m.pid --pythonpath >
          ├─1008523 /opt/openl2m/venv/bin/python3 /opt/openl2m/venv/bin/gunicorn --pid /var/tmp/openl2m.pid --pythonpath >
          ├─1008524 /opt/openl2m/venv/bin/python3 /opt/openl2m/venv/bin/gunicorn --pid /var/tmp/openl2m.pid --pythonpath >
          └─1008525 /opt/openl2m/venv/bin/python3 /opt/openl2m/venv/bin/gunicorn --pid /var/tmp/openl2m.pid --pythonpath >

  Oct 25 23:37:56 openl2m-server systemd[1]: Started OpenL2M - Open Layer 2 Switch Management WSGI Service.


If all is well, you are now ready to install the :doc:`webserver <nginx>`.
