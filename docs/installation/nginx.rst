.. image:: ../_static/openl2m_logo.png

=====
Nginx
=====

Installation of the web server has two components:

#. Nxgin web server
#. Gunicorn WSGI process or gateway

**WSGI Service Installation**
OpenL2M has only been tested running as a WSGI service under the Nginx web server.

We use gunicorn_ as the WSGI gateway service. This basically runs the OpenL2m Python code as a service process
with a WSGI interface. The Nginx web server talks in the backend to this WSGI interface to render client http requests.
Gunicorn is started as a service from systemd.
(Note that Apache web server should work fine, but is left as an exercise to the reader.)

.. _gunicorn: http://gunicorn.org/

**Nginx Web Server Installation**

The following will serve as a minimal nginx configuration.
Be sure to modify your server name and installation path appropriately.

CentOS
======

**CentOS 7**
The following will serve as a minimal nginx configuration. The EPEL repo provides Nginx for CentOS7
Be sure to modify your server name and installation path appropriately:

.. code-block:: bash

  # yum install epel-release
  # yum install nginx --enablerepo=epel

**CentOS 8**
Here, you need:

.. code-block:: bash

  # dnf install nginx

(See more at https://linuxconfig.org/install-nginx-on-redhat-8)

**Run OpenL2M on regular non-secured port**

Once nginx is installed, save the following configuration to `/etc/nginx/conf.d/openl2m.conf`.
Be sure to replace `openl2m.yourcompany.com` with the domain name or IP address of your installation.
(This should match the value configured for `ALLOWED_HOSTS` in `configuration.py`.)
Adjust the listening port as needed (e.g. change 80 to 8000)
The file *openl2m.conf* is available in this directory:

.. code-block:: bash

  server {
    listen 80;

    server_name openl2m.yourcompany.com;

    client_max_body_size 25m;

    location /static/ {
        alias /opt/openl2m/openl2m/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_pass_header X-CSRFToken;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
        proxy_connect_timeout       300;
        proxy_send_timeout          300;
        proxy_read_timeout          300;
        send_timeout                300;
    }
  }

Note that the configuration above sets various timeouts to 5 minutes.
This is to make sure the OpenL2M django process has enough time to poll the switch SNMP tables.
Large stacks of switches can take up to 1 minute or more to poll data via SNMP.
Please adjust these timeouts as appropriate for your environment

Next, if you do not want the default web site, edit the `/etc/nginx/nginx.conf` file,
and remove or comment out this section:

.. code-block:: bash

  server {
      listen       80 default_server;
      ...
    }

Test the new config:

.. code-block:: bash

  # nginx -t

Restart the nginx service to use the new configuration:

.. code-block:: bash

  # systemctl restart nginx
  # systemctl enable nginx

We highly recommend you `enable SSL <nginx-ssl>`

**firewalld configuration**

You will need to allow the standard http (and https) ports through the firewall, assuming you run this.
To configure allowing this, run:

.. code-block:: bash

  # firewall-cmd --zone=public --permanent --add-service=http
  # firewall-cmd --zone=public --permanent --add-service=https
  # firewall-cmd --reload

If you do any kind of testing with the django built-in web server (e.g. python3 manage.py runserver 0:8000),
make sure you open the proper port:

.. code-block:: bash

  # firewall-cmd --zone=public --permanent --add-port=8000/tcp
  # firewall-cmd --reload



**gunicorn Installation**

Install gunicorn:

.. code-block:: bash

  # pip3 install gunicorn

The Gunicorn configuration is in the root openl2m installation path as `gunicorn_config.py`
(e.g. `/opt/openl2m/gunicorn_config.py` per our example installation).

Verify the location of the gunicorn executable on your server (e.g. `which gunicorn`)
And update the `pythonpath` variable if needed:

.. code-block:: bash

  command = '/usr/local/bin/gunicorn'
  pythonpath = '/opt/openl2m/openl2m'
  bind = '127.0.0.1:8001'
  workers = 3
  user = 'nginx'
  timeout = 150
  #errorlog = '/var/log/gunicorn_errors.log'

Notes:
The number of workers is related to how many users your site wil service at the same time.
If this is large, increase the 3 to something higher, and restart the service (see below)

Note that the timeout is increased from the default 30 seconds, to 150.
This is to allow large switch stacks to be polled without causing a process timeout.
You may need to adjust this timeout to suit your environment.

**systemd configuration**

We will install Gunicorn as a service under systemd. The systemd service definition is in the file 'openl2m.service'.
See this github page for more details: https://github.com/netbox-community/netbox/issues/2902

Copy the file *openl2m.service* to the */etc/systemd/system* directory:

.. code-block:: bash

  # cp openl2m.service /etc/systemd/system

Now activate this service:

.. code-block:: bash

  systemctl daemon-reload
  systemctl start openl2m
  systemctl enable openl2m

And verify:

.. code-block:: bash

  systemctl status openl2m

**Debugging**

First of all, if you get a 502-Bad Gateway, you should check your SeLinux setup. It is likely that
your gunicorn process needs to be white-listed. Something like this may work:

.. code-block:: bash

  # setsebool httpd_can_network_connect on -P

You can enable the errorlog setting commented out above. Edit the file,
and don't forget to restart the process with:

.. code-block:: bash

  systemctl restart openl2m

You can check the content of the error log file and see if there are timeout warnings in it.
If you, increase the timeout, and restart. Don't forget to turn off error logging when you have
found the timeout value that works well in your environment.

**Finish it**

At this point, you should be able to connect to the nginx HTTP service at the server name or IP address you provided.
If you are unable to connect, check that the nginx service is running and properly configured.
Additionally,  make sure your firewalld is properly configured!
If you receive a 502 (bad gateway) error, this indicates that gunicorn is misconfigured or not running.

Please keep in mind that the configurations provided here are bare minimums required to get openl2m up and running.
You will almost certainly want to make some changes to better suit your production environment.

If all is well, you are now ready to run the application. Point your browser to it,
and login as admin. **We strongly recommend you import a few test switches to
check that everything functions as you expect, before you start using this in production!**

Finally, Have Fun!

:doc:`We strongly recommend that you use SSL encryption on your web server. <nginx-ssl>`

If you decide to do so, you can now optionally :doc:`use LDAP for authentication. <ldap>`

Also optionally, you can allow users to :doc:`schedule bulk changes at some time in the future. <tasks>` 

If all is well, you are now ready to install the :doc:`webserver <nginx>`.
