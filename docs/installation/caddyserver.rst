.. image:: ../_static/openl2m_logo.png

==================
Caddy Installation
==================
At this time, the Gunicorn Python gateway service should be running.
Caddyserver ("Caddy") be used to proxy that WSGI service. Configuration is not well documented at this time.

The following will serve as a minimal Caddy configuration.
Be sure to modify your caddyserver configuration appropriately.

Follow the steps outlined here to install Caddy:  https://caddyserver.com/docs/install

.. note::

  The configuration below assumes that Caddy can do it's "auto SSL" magic, ie install automatic,
  free "Let's Encrypt" SSL certificates!

  YOU SHOULD NOT USE THIS Caddyfile IF YOU CANNOT GET AUTOMATIC SSL ENCRYPTION!
  For custom SSL installs, or better yet SSL using the ACME protocol:

  Refer to the Caddy docs for more information:
  https://caddyserver.com/docs/caddyfile


Configuration
-------------

**Run OpenL2M on regular non-secured port**

The following assumed OpenL2M is the *only* web site running on this Caddy server.
*If you are using a multi-site setup of Caddy, we assume you know what you need to configure to get OpenL2M functional!*

Backup the original Caddy config, and copy the OpenL2M configuration file. This creates a default web site for OpenL2M on port 80.

.. code-block:: bash

  sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup
  sudo cp ./scripts/Caddyfile /etc/caddy/Caddyfile


Restart the Caddy service to use the new configuration:

.. code-block:: bash

  sudo systemctl restart caddy
  sudo systemctl enable caddy


We highly recommend you enable SSL if auto-SSL is not working for your setup. Please refer to the Caddy documentation for details.

**Notes**

The configuration does not tweak various timeouts. If you experience OpenL2M timeouts,
please refer to the Caddy documentation for details on tweaking settings.

**Firewall configuration**

On your server, you will need to allow the standard http (tcp/80) and https (tcp/443) ports through the OS firewall:
To configure this on Ubuntu, see below. Other distros may vary in config.

**Ubuntu**

.. code-block:: bash

  sudo ufw allow http
  sudo ufw allow https


If you are behind an enterprise firewall, those same ports need to be allowed to your server!


Debugging
---------

First of all, if you get a 502-Bad Gateway, you should check your SeLinux setup. It is likely that
your gunicorn process needs to be white-listed. Something like this may work:

.. code-block:: bash

  sudo setsebool httpd_can_network_connect on -P

You can enable the errorlog setting commented out above. Edit the file,
and don't forget to restart the process with:

.. code-block:: bash

  sudo systemctl restart openl2m

You can check the content of the error log file and see if there are timeout warnings in it.
If you, increase the timeout, and restart. Don't forget to turn off error logging when you have
found the timeout value that works well in your environment.


Finish it
---------

At this point, you should be able to connect to the Caddy HTTP service at the server name or IP address you provided.
If you are unable to connect, check that the caddy service is running and properly configured.
Additionally,  make sure your firewalld is properly configured!
If you receive a 502 (bad gateway) error, this indicates that gunicorn is misconfigured or not running.

Please keep in mind that the configurations provided here are bare minimums required to get openl2m up and running.
You will almost certainly want to make some changes to better suit your production environment.

If all is well, you are now ready to run the application. Point your browser to it,
and login as admin. **We strongly recommend you import a few test switches to
check that everything functions as you expect, before you start using this in production!**

Finally, Have Fun!

**We strongly recommend that you use SSL encryption on your web server**

If you decide to do so, you can now optionally :doc:`use LDAP for authentication.<ldap>`

