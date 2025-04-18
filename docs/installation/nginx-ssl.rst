.. image:: ../_static/openl2m_logo.png

===========================
Nginx with SSL Certificates
===========================

We highly recommend that you run the OpenL2M application on a secure web server.
Here are steps to add a CA-signed SSL certificate to the Nginx configuration.
You can also use a self-signed certificate, but that is left as an exercise to the reader.

For more details, also see https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04

Note: if you want to run OpenL2M on an existing Nginx install that already has an SSL website on it,
you will need to look at the SNI or "Server Name Indication" capability. There are numerous tutorials
around that show you how to configure this.

**Django Configuration**

When you enable SSL, you need to add two settings to *openl2m/configuration.py* make SSL more secure:

.. code-block:: python

  # if using SSL, these should be set to True:
  CSRF_COOKIE_SECURE = True
  SESSION_COOKIE_SECURE = True

**Prepare Nginx for SSL**

First we create the directory to hold your SSL keys and certificate:

.. code-block:: bash

  sudo mkdir /etc/nginx/ssl
  cd /etc/nginx/ssl
  sudo chmod g-rwx,o-rws .

**This assumes your private key will be installed in /etc/nginx/ssl,
and that this directory is only accessible by the 'root' account.
If your organization has different security requirements,
change this as appropriate.**

**Create a strong Diffie-Hellman group**

Run the following command to generate a good base for the SSL encryption. This will take a while, be patient::


  sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

**Create a new Certificate Signing Request**

As root, run the following commands to create a CSR:

.. code-block:: bash

  cd /etc/nginx/ssl
  sudo openssl req -new -newkey rsa:2048 -nodes -keyout openl2m.key -out openl2m.csr

On the last line, we generate the CSR. Fill in the questions as applicable to your organization.

**Upload the CSR to your CA account**

You now need to login to your favorite Certificate Authority account to generate a signed SSL certificate from the CSR.
This process is very CA dependent, and will be left up to the reader.

**Install the Signed Certificate**

Once the certificate is issues or generated, download the X509 format file (\*.cer) to the /etc/nginx/ssl directory.
Name this file openl2m.crt


**Reconfigure for SSL**

Copy the "openl2m-ssl.conf" to nginx as a new site, and enable it:

.. code-block:: bash

  sudo cp ./scripts/openl2m-ssl.conf /etc/nginx/sites-available/openl2m-ssl
  sudo ln -s /etc/nginx/sites-available/openl2m-ssl /etc/nginx/sites-enabled/openl2m-ssl

Modify this files to set your proper domain name!

Next modify the regular port 80 default site to do a redirect to the SSL site:

.. code-block:: bash

  sudo vi /etc/nginx/sites-available/openl2m


and replace the content with the following. Note this is available in the scripts directory as *openl2m-redirect.conf*:

.. code-block:: bash

  server {
      listen 80;

      server_name openl2m.yourcompany.com;
      return 301 https://openl2m.yourcompany.com/;
  }

Again, modify your domain name accordingly!


**Finally, test the config**:

.. code-block:: bash

  sudo nginx -t


Solve any errors that may show. If all is OK, restart Nginx, and you should have an SSL web site up::

  sudo systemctl restart nginx


**Renewing your SSL certificate**

Renew the certificate at your CA> Download the new certificate in X509/.cer format. Replace the content of /etc/nginx/ssl/openl2m.crt with this new certificate.
Then restart nginx per the above.
