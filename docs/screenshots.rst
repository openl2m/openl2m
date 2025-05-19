.. image:: _static/openl2m_logo.png

===================
OpenL2M Screenshots
===================

* **Login Window:** Can show configurable login, top, and bottom banners.

.. image:: _static/login-window.png


* **Devices Menu:** Shows the groups and devices you can access

.. image:: _static/devices-menu.png

* **Dark Mode Devices Menu:** Dark Mode view of the groups and devices you can access

.. image:: _static/devices-menu-dark-mode.png

* **Interfaces Menu:** Edit a single interface at a time

.. image:: _static/interfaces-menu.png


* **Bulk-Edit Menu:** Edit multiple interfaces at once

.. image:: _static/bulkedit-menu.png


* **Commands Menu:** Run pre-defined commands on the device

.. image:: _static/commands-menu.png


* **Command Templates Menu:** Run pre-defined commands with user-input on the device

.. image:: _static/command-templates-menu.png


* **VLAN Edit Menu:** Add, Rename, or Delete vlans

.. image:: _static/vlan-edit.png


* **Device Connections Graph:**

.. mermaid::
    
    ---
    title: Device connections for 'ROUTER'
    ---
    flowchart LR
    DEVICE["ROUTER"]
    REMOTE_1["fa:fa-cogs Switch-1"]
    DEVICE_INTERFACE_1("Ten-GigabitEthernet1/0/1")
    REMOTE_INTERFACE_1("Ten-GigabitEthernet4/0/49")
    DEVICE --- DEVICE_INTERFACE_1
    DEVICE_INTERFACE_1 <==> REMOTE_INTERFACE_1
    REMOTE_INTERFACE_1 --- REMOTE_1

    REMOTE_2["fa:fa-cogs Switch-2"]
    DEVICE_INTERFACE_2("Ten-GigabitEthernet1/0/47")
    REMOTE_INTERFACE_2("Ten-GigabitEthernet1/0/52")
    DEVICE --- DEVICE_INTERFACE_2
    DEVICE_INTERFACE_2 <==> REMOTE_INTERFACE_2
    REMOTE_INTERFACE_2 --- REMOTE_2

    REMOTE_3["fa:fa-cog Switch-3"]
    DEVICE_INTERFACE_3("Ten-GigabitEthernet1/0/48")
    REMOTE_INTERFACE_3("Ten-GigabitEthernet1/0/51")
    DEVICE --- DEVICE_INTERFACE_3
    DEVICE_INTERFACE_3 <==> REMOTE_INTERFACE_3
    REMOTE_INTERFACE_3 --- REMOTE_3

    REMOTE_4["fa:fa-cogs Core-Router-1"]
    DEVICE_INTERFACE_4("HundredGigE1/0/53")
    REMOTE_INTERFACE_4("HundredGigE1/2/4")
    DEVICE --- DEVICE_INTERFACE_4
    DEVICE_INTERFACE_4 <==> REMOTE_INTERFACE_4
    REMOTE_INTERFACE_4 --- REMOTE_4

    REMOTE_5["fa:fa-cogs Core-Router-2"]
    DEVICE_INTERFACE_5("HundredGigE1/0/54")
    REMOTE_INTERFACE_5("HundredGigE1/2/4")
    DEVICE --- DEVICE_INTERFACE_5
    DEVICE_INTERFACE_5 <==> REMOTE_INTERFACE_5
    REMOTE_INTERFACE_5 --- REMOTE_5

