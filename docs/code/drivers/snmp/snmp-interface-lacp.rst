.. image:: ../../../_static/openl2m_logo.png

==============================
Discover interface LACP status
==============================

We call *self._get_lacp_data()* to read the device interface LACP membership, if any.
This info comes from the LAG MIB.

First, we read **dot3adAggActorAdminKey**. This gives us the ifIndex for any aggregate interfaces that exists
(aka Bridge-Aggregation, PortChannel, etc.)

If we find aggregate interfaces, then we walk **dot3adAggPortActorAdminKey**.

This gets the admin key or "index" for physical member interfaces. This maps back to the logical
or actor aggregates above in *dot3adAggActorAdminKey*