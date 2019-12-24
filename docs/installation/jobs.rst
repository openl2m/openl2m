.. image:: ../_static/openl2m_logo.png

========================
Bulk-Edit Job Scheduling
========================

To schedule Bulk Edit jobs at some time in the future, you need to install the Redis message queue,
and Celery scheduling.

Install Redis:

CentOS 7:

.. code-block:: bash

  yum install -y redis

CentOS8:

.. code-block:: bash

    dnf install -y redis

And then start and enable:

.. code-block:: bash

  systemctl enable redis
  systemctl start redis
  systemctl status redis


Install Celery:

.. code-block:: bash

  pip3 install celery[redis]


Test this from the ./openl2m/ directory (where manage.py lives).
You should see some lines indicating success:

.. code-block:: bash

  celery -A openl2m worker --loglevel info

  <...snip...>
  [2019-12-22 00:31:57,754: INFO/MainProcess] Connected to redis://localhost:6379//
  [2019-12-22 00:31:57,789: INFO/MainProcess] mingle: searching for neighbors
  [2019-12-22 00:31:58,848: INFO/MainProcess] mingle: all alone
  [2019-12-22 00:31:58,872: INFO/MainProcess] celery@your.host.name ready.
