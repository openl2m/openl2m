.. image:: ../../../_static/openl2m_logo.png

======================
Discover Hardware Info
======================

If hardware reading is enabled, the following function will read the standard ENTITY-MIB for hardware info,
see around line 1750:

.. code-block:: python

   retval = self._get_hardware_data()


As usual, entries are stored below the **entPhysicalEntry**, and are indexed for each attribute (ie. MIB entry).
We are only interested in a sub-set of attributes.

We first read **entPhysicalClass**, this returns the type of hardware at this index. We only store info about Stacks, Chassis or Module types.
This is stored in a **class StackMember()** object, saved in the **self.stack_members** Dict(), using the index as key.

.. code-block::

   hw_to_check = [ENTITY_CLASS_STACK, ENTITY_CLASS_CHASSIS, ENTITY_CLASS_MODULE]
   dprint("_parse_mibs_entity_physical()")
   dev_id = int(oid_in_branch(entPhysicalClass, oid))
   if dev_id:
      dev_type = int(val)
      if dev_type in hw_to_check:
            # save this info!
            member = StackMember(dev_id, dev_type)
            self.stack_members[dev_id] = member


Next we read **entPhysicalDescr**, **entPhysicalSerialNum**, **entPhysicalSoftwareRev** and **entPhysicalModelName**.
This is parsed in **_parse_mibs_entity_physical()**.

This reads a number of ENTITY-MIB entries, and fill in hardware data as desired in the appropriate self.stack_members[] Dict(),
based on the index being found.

