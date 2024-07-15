.. image:: ../_static/openl2m_logo.png

=======
The API
=======

This describes the use of the REST API to read and change settings of devices.

.. warning::

   The admin API can be used to read and create several types of objects with passwords,
   that due to the nature of their use, will be sent in plain text !

   We urge you to make sure your site uses SSL encryption, per your organizations' policy.


.. note::

   The REST API is truly RESTful! So NO data is being cached between calls,
   and each call will need to relearn the device. This can be slow!

.. toctree::
   :maxdepth: 1
   :caption: Here is what is available at this time:

   setup.rst
   endpoints.rst
   api_menu.rst
   api_search.rst
   api_basic_details.rst
   api_interface_state.rst
   api_interface_vlan.rst
   api_interface_poe.rst
   api_interface_description.rst
   api_save_config.rst
   api_vlan_manage.rst
   api_stats.rst
   api_environment.rst
   api_making_calls.rst
   api_user_token.rst
   admin/index.rst
