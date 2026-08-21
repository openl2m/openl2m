.. image:: ../../_static/openl2m_logo.png

=======
Caching
=======

In order to "speed up" rendering after the initial read of a device, (nearly) all data is cached in the WebUI session.
(Note: this implies also that the REST API does NOT use caching; it is truly RESTful!)

This caching is done via functions in *switches/connect/connector.py*,
see *save_cache()*, *load_cache()*, *set_do_not_cache_attribute()*, *set_cache_variable()*, *clear_cache()*

Session Caching in Django 5 uses the JSONSerializer. The most important thing to know here is that **if you add
Dictionary variables to the session cache, the keys of this Dict will be saved as strings** (Python str() class), regardless of the actual type!

I.e. if you have a dictionay with integer keys, upon storing and re-loading from the Session,
you will have a dictionary with str() keys! **This could have unexpected results when referencing this dictionary!**

Note: In general, drivers do not need to implement caching, as this is done in the base Connector() class.
