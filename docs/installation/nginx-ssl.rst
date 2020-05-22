.. image:: ../_static/openl2m_logo.png

===========================
Nginx with SSL Certificates
===========================

We highly recommend that you run the OpenL2M application on a secure web server.
Here are steps to add a CA-signed SSL certificate to the Nginx configuration.
You can also use a self-signed certificate, but that is left as an excercise to the reader.

For more details, also see https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04

**Prepare Nginx for SSL**

First we create the directory to hold your SSL keys and certificate:

.. code-block:: bash

  mkdir /etc/nginx/ssl
  cd /etc/nginx/ssl
  chmod g-rwx,o-rws .

**This assumes your private key is installed in /etc/nginx/ssl,
and that this directory is only accessible by the 'root' account.
If your organization has different security requirements,
change this as appropriate.**

**Create a strong Diffie-Hellman group**

Run the following command to generate a good base for the SSL encryption. This will take a while, be patient::


  openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

**Create a new Certificate Signing Request**

As root, run the following commands to create a CSR:

.. code-block:: bash

  cd /etc/nginx/ssl
  openssl req -new -newkey rsa:2048 -nodes -keyout openl2m.key -out openl2m.csr

On the last line, we generate the CSR. Fill in the questions as applicable to your organization.

**Upload the CSR to your CA account**

You now need to login to your favorite Certificate Authority account to generate a signed SSL certificate from the CSR.
This process is very CA dependent, and will be left up to the reader.

**Install the Signed Certificate**

Once the certificate is issues or generated, download the X509 format file to the /etc/nginx/ssl directory.
Name this file openl2m.cer


**Reconfigure for SSL**

Create the "openl2m-ssl.conf" nginx config file as follows:

.. code-block:: bash

  vi /etc/nginx/conf.d/openl2m-ssl.conf

Add the following section to this file. Note the complete file *openl2m-ssl.conf* is available in the scripts directory:

.. code-block:: bash

  server {
    listen 443 http2 ssl;

    server_name openl2m.yourcompany.com;
    ssl_certificate /etc/nginx/ssl/openl2m.crt;
    ssl_certificate_key /etc/nginx/ssl/openl2m.key;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;

    client_max_body_size 25m;

    location /static/ {
        alias /opt/openl2m/openl2m/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
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


Now modify the regular port to do a redirect to the SSL site:

.. code-block:: bash

  vi /etc/nginx/conf.d/openl2m.conf


and replace the content with the following. Note this is available in the scripts directory as *openl2m-redirect.conf*:

.. code-block:: bash

  server {
      listen 80;

      server_name openl2m.yourcompany.com;
      return 301 https://openl2m.yourcompany.com/;
  }


**Finally, test the config**:

.. code-block:: bash

  nginx -t


Solve any errors that may show. If all is OK, restart Nginx, and you should have an SSL web site up::

  systemctl restart nginx
