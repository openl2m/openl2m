.. image:: ../_static/openl2m_logo.png

==================
Nginx Installation
==================
At this time, the Gunicorn Python gateway service should be running. Nginx will be used to proxy that WSGI service.

The following will serve as a minimal nginx configuration.
Be sure to modify your server name and installation path appropriately.

**Ubuntu 20.04 LTS**

.. code-block:: bash

  sudo apt install -y nginx


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


Configure nginx
---------------

**Run OpenL2M on regular non-secured port**

Once nginx is installed, we need to configure the site. The following assumed OpenL2M is the *only* web site running on this server.
*If you are using a multi-site setup of nginx, we assume you know what you need to configure to get OpenL2M functional!*

Copy the configuration file:

.. code-block:: bash

  cp ./scripts/openl2m.conf /etc/nginx/sites-available/openl2m


(For multi-site, edit /etc/nginx/sites-enabled/openl2m, and set listen and hostname fields. The domain name or IP address should match the value configured for `ALLOWED_HOSTS` in `configuration.py`.)


Now remove the default site config, and set openl2m as the new default:

.. code-block:: bash

  rm /etc/nginx/site-enabled/default
  ln -s /etc/nginx/sites-available/openl2m /etc/nginx/sites-enabled/openl2m


Test the new config:

.. code-block:: bash

  # nginx -t


Restart the nginx service to use the new configuration:

.. code-block:: bash

  # systemctl restart nginx
  # systemctl enable nginx


We highly recommend you `enable SSL <nginx-ssl>`

**Notes**

The configuration used sets various timeouts to 5 minutes.
This is to make sure the OpenL2M django process has enough time to poll the switch SNMP tables.
Large stacks of switches can take up to 1 minute or more to poll data via SNMP.
Please adjust these timeouts as appropriate for your environment


**Firewall configuration**

You will need to allow the standard http (and https) ports through the firewall, assuming you run this.
To configure allowing this, run:

** Ubuntu 20.04 **

.. code-block:: bash

  # ufw allow http
  # ufw allow https


** CentOS 8 **

.. code-block:: bash

  # firewall-cmd --zone=public --permanent --add-service=http
  # firewall-cmd --zone=public --permanent --add-service=https
  # firewall-cmd --reload


Debugging
---------

First of all, if you get a 502-Bad Gateway, you should check your SeLinux setup. It is likely that
your gunicorn process needs to be white-listed. Something like this may work:

.. code-block:: bash

  # setsebool httpd_can_network_connect on -P

You can enable the errorlog setting commented out above. Edit the file,
and don't forget to restart the process with:

.. code-block:: bash

  sudo systemctl restart openl2m

You can check the content of the error log file and see if there are timeout warnings in it.
If you, increase the timeout, and restart. Don't forget to turn off error logging when you have
found the timeout value that works well in your environment.


Finish it
---------

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
