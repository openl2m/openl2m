.. image:: ../_static/openl2m_logo.png

Junos Driver Overview
=====================

The Junos driver uses the Juniper Py-EzNC library. We make extensive use of the
Tables and Views capability. We use several built-in tables, as well as some newly defined or modified Juniper tables.
See the references section for links, and especial the O'Reilly book Chapter 4 is useful!

The custom tables and views are located in the *resources* directory. Looks at the *.yml* for their definitions, and *.py* files
that allow for easy use. The identically named *.txt* files show the command line *show commands* that give details of
the rpc functions and their return data.
