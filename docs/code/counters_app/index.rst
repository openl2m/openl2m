.. image:: ../../_static/openl2m_logo.png

================
The counters app
================

The counters/ directory contains a really simple app to maintain some useage statistics, or any other kind of counter.

Most things here are 'standard' Django. We highlight just the needed parts:

**models.py**
We define the very simple Counter() class here, which has a value and a description.
We also provide a function to increase a specific counter, that can be used elsewhere.

Counters are defined in constants.py, and can be managed from the OpenL2M admin interface.

If you want to add a new counter, you *should* add it via a migration.
See e.g. *openl2m/counters/migrations/0001_initial.py*. This shows how to add
new counters.
